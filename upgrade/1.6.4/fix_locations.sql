--Delete building zi from AQDB since it doesn't exist in DSDB
DELETE FROM building WHERE id=(
    SELECT id FROM location WHERE location_type='building' AND name='zi');
DELETE FROM location WHERE id=(
    SELECT id FROM location WHERE location_type='building' AND name='zi');
commit;

-- Update middle east countries' continent/hub to europe (EMEA includes this)
-- (sa) Saudi Arabia
-- (qt) Qatar
-- (is) Israel
-- (eg) Egypt
-- (ae) UAE

UPDATE location SET parent_id = (
    SELECT id FROM location WHERE location_type='continent' AND name='eu')
WHERE location_type='country' AND name IN ('sa', 'qt', 'is', 'eg', 'ae');
commit;

