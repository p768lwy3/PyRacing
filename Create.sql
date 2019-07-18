CREATE TABLE HorseInfo (
    HorseId varchar(12) NOT NULL, 
    Name varchar(64), 
    Country varchar(3), 
    Age int, 
    Color varchar(16),
    Sex varchar(16), 
    ImportType varchar(3), 
    SeasonStakes int, 
    TotalStakes int, 
    Starts123 varchar(16),
    StartsPast10 int, 
--    Trainer varchar(64), 
    Owner varchar(64), 
    CurrentRating int, 
    StartRating int,
    Sire varchar(64), 
    Dam varchar(64), 
    DamSire varchar(64), 
    PRIMARY KEY(HorseId)
);

CREATE TABLE PastRecord (
    RaceId varchar(10) NOT NULL,
    HorseId varchar(12) NOT NULL,
--    RaceIndex int,
--    Pla int,
--    RaceDate DATE,
--    RC varchar(2),
--    Track varchar(8),
--    Course varchar(8),
--    Dist int,
--    G varchar(8),
--    RaceClass varchar(8),
--    Dr int,
    Rtg int,
    Trainer varchar(64),
    Jockey varchar(64),
--   LBW varchar(12),
--    WinOdds float,
    ActWt int,
    RunningPosition varchar(32),
--    FinishTime varchar(7),
    DeclarHorseWt int,
    Gear varchar(16),
    PRIMARY KEY(RaceId, HorseId)
);

CREATE TABLE RaceInfo (
    RaceId varchar(10) NOT NULL,
    RaceClass varchar(24),
    RaceDate DATE,
    Venue varchar(2)
    Track varchar(24), 
    Course varchar(24),
    Going varchar(24), 
    Dist int,
    PRIMARY KEY(raceId)
);

CREATE TABLE RaceResults (
    RaceID varchar(10) NOT NULL,
    HorseID varchar(12) NOT NULL,
    Pla int,
    HorseNo int, 
--    Jockey varchar(64),
--    Trainer varchar(64),
--    ActWt int,
--    DeclarHorseWt int,
    Draw int,
    LBW varchar(12),
    FinishTime varchar(7),
    WinOdds float,
    PRIMARY KEY(raceID, HorseID)
);
