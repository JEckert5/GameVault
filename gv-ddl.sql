CREATE TABLE `user` (
	userID int,
	username varchar(25),
	email varchar(30),
	password varchar(30),
	status ENUM('ONLINE','AWAY','DO NOT DISTURB','OFFLINE'),
	bio text,
	PRIMARY KEY (userID),
	UNIQUE KEY (username),
	UNIQUE KEY (email)
);

CREATE TABLE `library` (
	libraryID int,
	ownerID int,
	PRIMARY KEY (libraryID),
	FOREIGN KEY (ownerID) REFERENCES `user` (userID)
);

CREATE TABLE `developer` (
    developerID int,
    about text,
    PRIMARY KEY (developerID)
);

CREATE TABLE `game` (
    gameID int,
    title text,
    genre ENUM('FPS','Hack n Slash','RPG','Fighting'),
    description text,
    developerID int,
    total_checkpoints int,
    PRIMARY KEY (gameID),
    FOREIGN KEY (developerID) REFERENCES `developer` (developerID)
);

CREATE TABLE `owned_games` (
    gameID int,
    libraryID int,
    completed_checkpoints int,
    FOREIGN KEY (gameID) REFERENCES `game` (gameID),
    FOREIGN KEY (libraryID) REFERENCES `library` (libraryID)
);

CREATE TABLE `address` (
	id int,
	street_addr text,
	city text,
	territory text, -- state is a keyword I guess lol
	country text,
	PRIMARY KEY (id)
);

CREATE TABLE `payment_info` (
	paymentID int,
	userID int,
	card_num int,
	cvv int,
	exp_date date,
	billing_address int,
	PRIMARY KEY (paymentID),
	FOREIGN KEY (userID) REFERENCES `user` (userID),
	FOREIGN KEY (billing_address) REFERENCES `address` (id)
);

CREATE TABLE `transaction` (
	transID int,
	paymentID int,
	gameID int,
	payment_time timestamp,
	amnt_due real,
	subscription boolean,
	PRIMARY KEY (transID),
	FOREIGN KEY (paymentID) REFERENCES `payment_info` (paymentID),
	FOREIGN KEY (gameID) REFERENCES `game` (gameID)
);

CREATE TABLE `system_logs` (
	logID int,
	timestamp timestamp,
	ip int(4),
	status ENUM('LOG','WARNING','ERROR'),
	PRIMARY KEY (logID)
);