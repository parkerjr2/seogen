create table if not exists bulk_jobs (
  id uuid primary key default gen_random_uuid(),
  license_key text not null,
  site_url text,
  status text not null default 'pending',
  total_items int not null default 0,
  processed int not null default 0,
  completed int not null default 0,
  failed int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  job_name text
);

create index if not exists bulk_jobs_license_key_idx on bulk_jobs (license_key);

create table if not exists bulk_job_items (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references bulk_jobs(id) on delete cascade,
  idx int not null,
  service text not null,
  city text not null,
  state text not null,
  company_name text not null,
  phone text not null,
  address text not null,
  canonical_key text not null,
  status text not null default 'pending',
  result_json jsonb,
  error text,
  attempts int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (job_id, canonical_key)
);

create index if not exists bulk_job_items_job_id_idx on bulk_job_items (job_id);
create index if not exists bulk_job_items_canonical_key_idx on bulk_job_items (canonical_key);
create index if not exists bulk_job_items_status_idx on bulk_job_items (status);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists bulk_jobs_set_updated_at on bulk_jobs;
create trigger bulk_jobs_set_updated_at
before update on bulk_jobs
for each row execute function set_updated_at();

drop trigger if exists bulk_job_items_set_updated_at on bulk_job_items;
create trigger bulk_job_items_set_updated_at
before update on bulk_job_items
for each row execute function set_updated_at();
