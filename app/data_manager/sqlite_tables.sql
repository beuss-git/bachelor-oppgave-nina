CREATE TABLE video (
 id TEXT PRIMARY KEY,
 title TEXT NOT NULL,
 date DATETIME NOT NULL,
 totaldetections INTEGER NOT NULL,
 videolength TIME NOT NULL,
 outputvideolength TIME NOT NULL
);

CREATE TABLE detection (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 videoid TEXT NOT NULL,
 starttime TIME NOT NULL,
 endtime TIME NOT NULL,
 FOREIGN KEY (videoid) REFERENCES video(id)
);
