update host set operating_system_id = 2 where operating_system_id = 6 and personality_id in(select id from personality where archetype_id=1);

commit;

