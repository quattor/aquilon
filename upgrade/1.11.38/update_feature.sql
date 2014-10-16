UPDATE FEATURE SET VISIBILITY = 'owner_approved' where VISIBILITY='owner-approved';
UPDATE FEATURE SET VISIBILITY = 'owner_only' where VISIBILITY='owner-only';
COMMIT;
EXIT;
