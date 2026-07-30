create extension if not exists vector;

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'New conversation',
  is_public boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  image_url text,
  image_name text,
  symptom_summary jsonb,
  citations jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references auth.users(id) on delete set null,
  source text not null,
  title text not null,
  url text,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  content text not null,
  embedding vector(1536),
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists public.conversation_sources (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  message_id uuid references public.messages(id) on delete cascade,
  document_id uuid references public.documents(id) on delete set null,
  source text not null,
  title text not null,
  year text,
  category text not null,
  url text,
  summary text not null,
  evidence_level text not null,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.conversation_sources enable row level security;

create policy "users read own or public conversations"
on public.conversations for select
using (auth.uid() = user_id or is_public);

create policy "users manage own conversations"
on public.conversations for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "users read messages from visible conversations"
on public.messages for select
using (
  exists (
    select 1 from public.conversations c
    where c.id = conversation_id and (c.user_id = auth.uid() or c.is_public)
  )
);

create policy "users manage own messages"
on public.messages for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "authenticated users read documents"
on public.documents for select
using (auth.role() = 'authenticated');

create policy "authenticated users read document chunks"
on public.document_chunks for select
using (auth.role() = 'authenticated');

create policy "users read sources from visible conversations"
on public.conversation_sources for select
using (
  exists (
    select 1 from public.conversations c
    where c.id = conversation_id and (c.user_id = auth.uid() or c.is_public)
  )
);

create policy "users write sources for own conversations"
on public.conversation_sources for insert
with check (
  exists (
    select 1 from public.conversations c
    where c.id = conversation_id and c.user_id = auth.uid()
  )
);

create index if not exists conversations_user_updated_idx on public.conversations (user_id, updated_at desc);
create index if not exists messages_conversation_created_idx on public.messages (conversation_id, created_at);
create index if not exists conversation_sources_conversation_idx on public.conversation_sources (conversation_id, created_at desc);
create index if not exists document_chunks_embedding_idx on public.document_chunks using ivfflat (embedding vector_cosine_ops);
