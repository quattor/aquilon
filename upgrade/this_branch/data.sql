/*
 * Prior to this branch, there was a vmhost archetype and no
 * cluster archetypes. So, we need to create new archetypes (and
 * personalities) for the existing data. New cluster types (e.g.
 * vcs, hadoop, etc) can be created via normal operational commands
 * so that means it's only the esx cluster (the only existing
 * cluster type) that needs to be transformed
 *
 * This script must be run AFTER the schema changes since it assumes
 * the new schema.
 */

INSERT INTO archetype
 (id, name, outputdesc, is_compileable, cluster_type, creation_date,
  comments)
VALUES
 (archetype_id_seq.nextval, 'esx_cluster', 'ESX', 1, 'esx', sysdate,
  'Created by upgrade script');

INSERT INTO personality
 (id, name, archetype_id, cluster_required, creation_date, comments)
VALUES
 (prsnlty_seq.nextval, 'vulcan-v1-1g-prod',
   (select id from archetype where name = 'esx_cluster'),
   0, sysdate, 'Created by upgrade script');

INSERT INTO personality
 (id, name, archetype_id, cluster_required, creation_date, comments)
VALUES
 (prsnlty_seq.nextval, 'vulcan-v1-10g-prod',
   (select id from archetype where name = 'esx_cluster'),
   0, sysdate, 'Created by upgrade script');

INSERT INTO clstr_allow_per
    (cluster_id, creation_date, personality_id)
SELECT id, sysdate, personality_id
FROM clstr;

UPDATE clstr SET personality_id =
      (select id from personality where name='vulcan-v1-10g-prod' and
       archetype_id = (select id from archetype where name = 'esx_cluster'))
      where personality_id in
            (select id from personality where name like '%-10g-%');

UPDATE clstr SET personality_id =
      (select id from personality where name='vulcan-v1-1g-prod' and
       archetype_id = (select id from archetype where name = 'esx_cluster'))
      where personality_id !=
            (select id from personality where name='vulcan-v1-10g-prod');

COMMIT;

