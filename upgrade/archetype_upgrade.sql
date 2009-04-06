ALTER TABLE ARCHETYPE ADD (IS_COMPILEABLE NUMBER(*,0));

UPDATE ARCHETYPE SET is_compileable=1 where name ='aquilon' ;
commit;

UPDATE ARCHETYPE SET is_compileable=0 where name != 'aquilon';
commit;

ALTER TABLE ARCHETYPE add constraint ARCHETYPE_IS_COMPILEABLE_NN check(IS_COMPILEABLE IS NOT NULL) ENABLE;
commit;

exit;
