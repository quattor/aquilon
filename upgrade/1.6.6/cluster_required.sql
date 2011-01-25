ALTER TABLE archetype ADD cluster_required NUMBER(*,0);
UPDATE archetype SET cluster_required = 0;
UPDATE archetype SET cluster_required = 1 WHERE name = 'vmhost';
ALTER TABLE archetype ADD CONSTRAINT "ARCHETYPE_CLUSTER_REQUIRED_CK"
    CHECK (cluster_required IN (0, 1)) ENABLE;
ALTER TABLE archetype MODIFY (cluster_required CONSTRAINT "ARCHETYPE_CLUSTER_REQUIRED_NN" NOT NULL ENABLE);
COMMIT;
