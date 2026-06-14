-- =====================================================================
-- Apelido (nickname) do usuário
--
-- O nome completo passa a ser usado somente no cadastro; o apelido
-- (mais curto) é o nome de exibição em toda a aplicação (sidebar,
-- ranking, dashboards).
-- =====================================================================

alter table public.profiles add column nickname text not null default '';
alter table public.profiles alter column nickname drop default;

create unique index profiles_nickname_key on public.profiles (nickname);

-- handle_new_user: também grava o apelido informado no cadastro
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, nome_completo, nickname, email, telefone, perfil)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'nome_completo', ''),
    coalesce(new.raw_user_meta_data ->> 'nickname', ''),
    new.email,
    coalesce(new.raw_user_meta_data ->> 'telefone', ''),
    'participante'
  );
  return new;
end;
$$;

-- v_ranking: usa o apelido (menor) em vez do nome completo para exibição
drop view public.v_ranking;

create view public.v_ranking as
select
  pr.id as user_id,
  pr.nickname,
  coalesce(sum(p.pontos), 0) as pontos_total,
  count(*) filter (where p.pontos = 3) as placares_exatos,
  count(*) filter (where p.pontos = 1) as acertos_vencedor,
  rank() over (order by coalesce(sum(p.pontos), 0) desc) as posicao
from public.profiles pr
left join public.predictions p on p.user_id = pr.id
where pr.perfil = 'participante' and pr.ativo
group by pr.id, pr.nickname;

revoke all on public.v_ranking from anon, authenticated, public;
grant select on public.v_ranking to authenticated;
