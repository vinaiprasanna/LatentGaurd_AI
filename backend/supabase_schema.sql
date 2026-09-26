create table if not exists public.audit_jobs (
    job_id text primary key,
    created_at timestamptz not null,
    record jsonb not null,
    results jsonb not null
);

create index if not exists audit_jobs_created_at_idx
    on public.audit_jobs (created_at desc);

create table if not exists public.review_actions (
    action_id text primary key,
    created_at timestamptz not null,
    record jsonb not null
);

create index if not exists review_actions_created_at_idx
    on public.review_actions (created_at desc);