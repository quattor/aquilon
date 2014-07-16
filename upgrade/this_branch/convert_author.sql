ALTER TABLE clstr ADD sandbox_author_id_new INTEGER;
ALTER TABLE clstr DROP CONSTRAINT cluster_sandbox_author_fk;

UPDATE clstr SET sandbox_author_id_new = (
		SELECT userinfo.id
		FROM userinfo, user_principal
		WHERE userinfo.name = user_principal.name AND user_principal.id = clstr.sandbox_author_id)
	WHERE sandbox_author_id IS NOT NULL;

SELECT count(sandbox_author_id_new) AS "Clusters in a sandbox" FROM clstr;

ALTER TABLE clstr ADD CONSTRAINT cluster_sandbox_author_fk FOREIGN KEY (sandbox_author_id_new) REFERENCES userinfo (id) ON DELETE SET NULL;
ALTER TABLE clstr DROP COLUMN sandbox_author_id;
ALTER TABLE clstr RENAME COLUMN sandbox_author_id_new TO sandbox_author_id;

ALTER TABLE host ADD sandbox_author_id_new INTEGER;
ALTER TABLE host DROP CONSTRAINT host_sandbox_author_fk;

UPDATE host SET sandbox_author_id_new = (
		SELECT userinfo.id
		FROM userinfo, user_principal
		WHERE userinfo.name = user_principal.name AND user_principal.id = host.sandbox_author_id)
	WHERE sandbox_author_id IS NOT NULL;

SELECT count(sandbox_author_id_new) AS "Hosts in a sandbox" FROM host;

ALTER TABLE host ADD CONSTRAINT host_sandbox_author_fk FOREIGN KEY (sandbox_author_id_new) REFERENCES userinfo (id) ON DELETE SET NULL;
ALTER TABLE host DROP COLUMN sandbox_author_id;
ALTER TABLE host RENAME COLUMN sandbox_author_id_new TO sandbox_author_id;

QUIT;
