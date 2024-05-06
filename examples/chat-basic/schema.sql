DROP TABLE IF EXISTS activity;



-- name
-- required String, in form	The name of the activity.
-- type
-- String, in form	Type of activity. For example - Run, Ride etc.
-- sport_type
-- required String, in form	Sport type of activity. For example - Run, MountainBikeRide, Ride, etc.
-- start_date_local
-- required Date, in form	ISO 8601 formatted date time.
-- elapsed_time
-- required Integer, in form	In seconds.
-- description
-- String, in form	Description of the activity.
-- distance
-- Float, in form	In meters.

CREATE TABLE activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  sport_type TEXT NOT NULL,
  start_date_local TIMESTAMP NOT NULL,
  elapsed_time INTEGER NOT NULL,
  description TEXT NOT NULL,
  distance FLOAT NOT NULL
);