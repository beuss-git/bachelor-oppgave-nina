CREATE TABLE video (
 id INTEGER PRIMARY KEY,
 title TEXT NOT NULL,
 date DATETIME NOT NULL,
 videolength TIME NOT NULL
);

CREATE TABLE detection (
 id INTEGER PRIMARY KEY,
 videoid INT NOT NULL,
 starttime TIME NOT NULL,
 endtime TIME NOT NULL,
 FOREIGN KEY (videoid) REFERENCES video(id)
);
