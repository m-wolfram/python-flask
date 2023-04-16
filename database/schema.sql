PRAGMA foreign_keys=on;


drop table if exists posts;
drop table if exists users;
drop table if exists profiles;
drop table if exists posts_likes;
drop table if exists files;


CREATE TABLE "posts" (
	"id" integer,
	"author_id" integer,
	"text" text NOT NULL,
	"date" text NOT NULL,
	FOREIGN KEY("author_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "users" (
	"id" integer,
	"username" text NOT NULL UNIQUE,
	"password_hash"	blob NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "profiles" (
    "id" integer,
    "user_id" integer UNIQUE,
    "first_name" text NOT NULL,
    "last_name" text NOT NULL,
    "gender" text NOT NULL,
    "birthdate" text NOT NULL,
    "bio" text NOT NULL,
    "registration_date" text NOT NULL,
    FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "posts_likes" (
    "id" integer,
    "post_id" integer NOT NULL,
    "like_author_id" integer NOT NULL,
    FOREIGN KEY("post_id") REFERENCES "posts"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY("like_author_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "files" (
    "id" integer,
    "original_file_name" text NOT NULL,
    "unique_file_name" text NOT NULL,
    "size_in_bytes" integer NOT NULL,
    "owner_id" text NOT NULL,
    "privacy" text NOT NULL,
    "upload_date" text NOT NULL,
    "expires" text NOT NULL,
    "description" text,
    FOREIGN KEY("owner_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY("ID" AUTOINCREMENT)
);
