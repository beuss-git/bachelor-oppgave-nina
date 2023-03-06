CREATE TABLE video (
 id TEXT PRIMARY KEY,
 title TEXT NOT NULL,
 date DATETIME NOT NULL,
 videolength TIME NOT NULL
);

CREATE TABLE detection (
 id TEXT PRIMARY KEY,
 videoid TEXT NOT NULL,
 starttime TIME NOT NULL,
 endtime TIME NOT NULL,
 FOREIGN KEY (videoid) REFERENCES video(id)
);
