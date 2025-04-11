-- Creating a user account, inputs would be taken from from in flask
INSERT INTO `user` (`username`, `email`, `password`, `status`, `bio`) VALUES (
    'jeckert5',
    'jeckert5@kent.edu',
    'password1234!',
    'ONLINE',
    'This is a test.'
);

-- User adding payment info and billing address
INSERT INTO `address` (`street_addr`, `city`, `state`, `country`) VALUES ('800 E Summit St', 'Kent', 'OH', 'USA');

INSERT INTO `payment_info` (`userID`, `card_num`, `cvv`, `exp_date`, `billing_address`) 
VALUES (
    1, 
    '1111222233334444', 
    '123', 
    '2029-4-1', 
    1
);

-- Developer adding a game
INSERT INTO `developer` (`name`, `about`) VALUES ('Valve', 'The goat');

INSERT INTO `game` (`title`, `genre`, `description`, `developerID`, `total_checkpoints`) 
VALUES (
    'Half-Life 2', 'FPS', 'Gordon Freeman goes to Costco', 1, 10
);


-- User Purchasing a game. Need userID, gameID, and payment info
INSERT INTO `transaction` (`paymentID`, `payment_time`, `amnt_due`, `subscription`, `item_purchased`)
VALUES (
    1, '2025-4-10 10:30:30.000000', 40, false, 1
);