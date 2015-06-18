SET serveroutput on;

ALTER TABLE parameter DROP CONSTRAINT parameter_personality_stage_uk;
DROP INDEX parameter_personality_stage_uk;

CREATE INDEX parameter_pers_st_idx ON parameter (personality_stage_id);

ALTER TABLE parameter ADD param_def_holder_id INTEGER;

DECLARE
	CURSOR param_curs IS
		SELECT param_def_holder.id AS defholder_id,
			personality_stage.id AS personality_stage_id,
			parameter.value, parameter.creation_date, parameter.holder_type
		FROM param_def_holder
			JOIN personality ON personality.archetype_id = param_def_holder.archetype_id
			JOIN personality_stage ON personality_stage.personality_id = personality.id
			LEFT OUTER JOIN parameter ON parameter.personality_stage_id = personality_stage.id
		WHERE param_def_holder."TYPE" = 'archetype'
		UNION ALL
		SELECT param_def_holder.id AS defholder_id,
			personality_stage.id AS personality_stage_id,
			parameter.value, parameter.creation_date, parameter.holder_type
		FROM param_def_holder
			JOIN feature_link ON feature_link.feature_id = param_def_holder.feature_id
			JOIN personality_stage ON personality_stage.id = feature_link.personality_stage_id
			LEFT OUTER JOIN parameter ON parameter.personality_stage_id = personality_stage.id
		WHERE param_def_holder."TYPE" = 'feature';
	param_rec param_curs%ROWTYPE;
	cnt NUMBER;
BEGIN
	cnt := 0;
	FOR param_rec IN param_curs LOOP
		IF param_rec.value IS NULL THEN
			-- The personality did not have any parameters before - create an empty record
			INSERT INTO parameter (id, param_def_holder_id, value, creation_date, holder_type, personality_stage_id)
				VALUES (parameter_id_seq.NEXTVAL,
					param_rec.defholder_id,
					'{}', CURRENT_DATE, 'personality', param_rec.personality_stage_id);
		ELSE
			INSERT INTO parameter (id, param_def_holder_id, value, creation_date, holder_type, personality_stage_id)
				VALUES (parameter_id_seq.NEXTVAL,
					param_rec.defholder_id,
					param_rec.value, param_rec.creation_date, param_rec.holder_type, param_rec.personality_stage_id);
		END IF;
		cnt := cnt + 1;
	END LOOP;
	DBMS_OUTPUT.PUT_LINE('Converted ' || TO_CHAR(cnt) || ' parameter records');
END;
/

DELETE FROM parameter WHERE param_def_holder_id IS NULL;

ALTER TABLE parameter ADD CONSTRAINT parameter_param_def_holder_fk FOREIGN KEY (param_def_holder_id) REFERENCES param_def_holder (id);
ALTER TABLE parameter MODIFY (param_def_holder_id CONSTRAINT parameter_pd_holder_id_nn NOT NULL);

ALTER TABLE parameter ADD CONSTRAINT parameter_pd_holder_pers_st_uk UNIQUE (param_def_holder_id, personality_stage_id);

QUIT;
