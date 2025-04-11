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

-- Make a trigger on insert that like checks for duplicates or something
CREATE TABLE `friends` (
	friend1 int,
	friend2 int,
	date_friended date,
	FOREIGN KEY (friend1) REFERENCES `user` (userID),
	FOREIGN KEY (friend2) REFERENCES `user` (userID)
);

CREATE TABLE `developer` (
    developerID int,
	name varchar(30),
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

CREATE TABLE `owned_game` (
    gameID int,
	ownerID int,
    completed_checkpoints int,
    FOREIGN KEY (gameID) REFERENCES `game` (gameID),
	FOREIGN KEY (ownerID) REFERENCES `user` (userID)
);

CREATE TABLE `address` (
	id int,
	street_addr text,
	city text,
	state text,
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
	item_purchased int,
	payment_time timestamp,
	amnt_due real,
	subscription boolean,
	PRIMARY KEY (transID),
	FOREIGN KEY (paymentID) REFERENCES `payment_info` (paymentID),
	FOREIGN KEY (item_purchased) REFERENCES `game` (gameID)
);

CREATE TABLE `review` (
	reviewID int,
	game int,
	user int,
	content text,
	title varchar(30),
	rating ENUM('POSITIVE','NEGATIVE'),
	PRIMARY KEY (reviewID),
	FOREIGN KEY (game) REFERENCES `game` (gameID),
	FOREIGN KEY (user) REFERENCES `user` (userID)
);

CREATE TABLE `comments` (
	commentID int,
	review int,
	user int,
	content text,
	PRIMARY KEY (commentID),
	FOREIGN KEY (review) REFERENCES `review` (reviewID),
	FOREIGN KEY (user) REFERENCES `user` (userID)
);