-- MySQL dump 10.13  Distrib 9.3.0, for Win64 (x86_64)
--
-- Host: localhost    Database: sae23_kuliha
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `editeurs`
--

DROP TABLE IF EXISTS `Editeurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Editeurs` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(100) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Nom` (`Nom`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Genres`
--

DROP TABLE IF EXISTS `Genres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Genres` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(50) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Nom` (`Nom`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Plateformes`
--

DROP TABLE IF EXISTS `Plateformes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Plateformes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(50) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Nom` (`Nom`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Utilisateurs`
--

DROP TABLE IF EXISTS `Utilisateurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Utilisateurs` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(100) NOT NULL,
  `Mot_de_passe` varchar(255) NOT NULL COMMENT 'Stocker un hash sécurisé (ex : bcrypt, argon2)',
  `Role` enum('Utilisateur','Admin') DEFAULT 'Utilisateur',
  `Dernier_acces` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Nom` (`Nom`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Jeux`
--

DROP TABLE IF EXISTS `Jeux`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Jeux` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Titre` varchar(100) NOT NULL,
  `Description` text,
  `Temps_moyen_termine` int DEFAULT '0',
  `Genre_ID` int NOT NULL,
  `Editeur_ID` int NOT NULL,
  `Plateforme_ID` int NOT NULL,
  `Ajoute_par` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `unique_jeu` (`Titre`,`Plateforme_ID`),
  KEY `Genre_ID` (`Genre_ID`),
  KEY `Editeur_ID` (`Editeur_ID`),
  KEY `Plateforme_ID` (`Plateforme_ID`),
  KEY `Ajoute_par` (`Ajoute_par`),
  CONSTRAINT `Jeux_ibfk_1` FOREIGN KEY (`Genre_ID`) REFERENCES `Genres` (`ID`),
  CONSTRAINT `Jeux_ibfk_2` FOREIGN KEY (`Editeur_ID`) REFERENCES `Editeurs` (`ID`),
  CONSTRAINT `Jeux_ibfk_3` FOREIGN KEY (`Plateforme_ID`) REFERENCES `Plateformes` (`ID`),
  CONSTRAINT `Jeux_ibfk_4` FOREIGN KEY (`Ajoute_par`) REFERENCES `Utilisateurs` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ListePerso`
--

DROP TABLE IF EXISTS `ListePerso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ListePerso` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Utilisateur_ID` int NOT NULL,
  `Jeu_ID` int DEFAULT NULL,
  `Ajoute_le` datetime DEFAULT CURRENT_TIMESTAMP,
  `Etat` enum('Non commencé','En cours','Terminé','Abandonné') DEFAULT 'Non commencé',
  `Note_personnelle` text,
  PRIMARY KEY (`ID`),
  KEY `Utilisateur_ID` (`Utilisateur_ID`),
  KEY `Jeu_ID` (`Jeu_ID`),
  CONSTRAINT `ListePerso_ibfk_1` FOREIGN KEY (`Utilisateur_ID`) REFERENCES `Utilisateurs` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `ListePerso_ibfk_2` FOREIGN KEY (`Jeu_ID`) REFERENCES `Jeux` (`ID`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `JeuxPersoManuels`
--

DROP TABLE IF EXISTS `JeuxPersoManuels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `JeuxPersoManuels` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `ListePerso_ID` int NOT NULL,
  `Titre` varchar(100) NOT NULL,
  `Description` text,
  `Genre` varchar(50) DEFAULT NULL,
  `Editeur` varchar(50) DEFAULT NULL,
  `Plateforme` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `ListePerso_ID` (`ListePerso_ID`),
  CONSTRAINT `JeuxPersoManuels_ibfk_1` FOREIGN KEY (`ListePerso_ID`) REFERENCES `ListePerso` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PartagesJeux`
--

DROP TABLE IF EXISTS `PartagesJeux`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PartagesJeux` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `De_Utilisateur_ID` int NOT NULL,
  `Vers_Utilisateur_ID` int NOT NULL,
  `ListePerso_ID` int NOT NULL,
  `Message` text,
  `Date_partage` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  KEY `De_Utilisateur_ID` (`De_Utilisateur_ID`),
  KEY `Vers_Utilisateur_ID` (`Vers_Utilisateur_ID`),
  KEY `ListePerso_ID` (`ListePerso_ID`),
  CONSTRAINT `PartagesJeux_ibfk_1` FOREIGN KEY (`De_Utilisateur_ID`) REFERENCES `Utilisateurs` (`ID`),
  CONSTRAINT `PartagesJeux_ibfk_2` FOREIGN KEY (`Vers_Utilisateur_ID`) REFERENCES `Utilisateurs` (`ID`),
  CONSTRAINT `PartagesJeux_ibfk_3` FOREIGN KEY (`ListePerso_ID`) REFERENCES `ListePerso` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SuggestionsJeux`
--

DROP TABLE IF EXISTS `SuggestionsJeux`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SuggestionsJeux` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Titre` varchar(100) NOT NULL,
  `Description` text,
  `Genre_ID` int DEFAULT NULL,
  `Editeur_ID` int DEFAULT NULL,
  `Plateforme_ID` int DEFAULT NULL,
  `Suggere_par` int DEFAULT NULL,
  `Temps_moyen_termine` int DEFAULT NULL,
  `Date_suggestion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  KEY `Genre_ID` (`Genre_ID`),
  KEY `Editeur_ID` (`Editeur_ID`),
  KEY `Plateforme_ID` (`Plateforme_ID`),
  KEY `Suggere_par` (`Suggere_par`),
  CONSTRAINT `SuggestionsJeux_ibfk_1` FOREIGN KEY (`Genre_ID`) REFERENCES `Genres` (`ID`),
  CONSTRAINT `SuggestionsJeux_ibfk_2` FOREIGN KEY (`Editeur_ID`) REFERENCES `Editeurs` (`ID`),
  CONSTRAINT `SuggestionsJeux_ibfk_3` FOREIGN KEY (`Plateforme_ID`) REFERENCES `Plateformes` (`ID`),
  CONSTRAINT `SuggestionsJeux_ibfk_4` FOREIGN KEY (`Suggere_par`) REFERENCES `Utilisateurs` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Insertion des données dans l'ordre des dépendances
--

-- 1. Tables indépendantes (sans clés étrangères)
-- Editeurs
INSERT IGNORE INTO `Editeurs` VALUES 
(1, 'Nintendo'),
(2, 'Sony Interactive Entertainment'),
(3, 'Ubisoft'),
(4, 'Electronic Arts'),
(5, 'Activision Blizzard'),
(6, 'Square Enix'),
(7, 'CD Projekt Red'),
(8, 'Bethesda'),
(9, 'Rockstar Games'),
(10, 'Capcom');

-- Genres
INSERT IGNORE INTO `Genres` VALUES 
(1, 'Action'),
(2, 'Aventure'),
(3, 'RPG'),
(4, 'FPS'),
(5, 'Sport'),
(6, 'Stratégie'),
(7, 'Simulation'),
(8, 'Course'),
(9, 'Plateforme'),
(10, 'Survival Horror');

-- Plateformes
INSERT IGNORE INTO `Plateformes` VALUES 
(1, 'PC'),
(2, 'PlayStation 5'),
(3, 'Xbox Series X'),
(4, 'Nintendo Switch'),
(5, 'PlayStation 4'),
(6, 'Xbox One'),
(7, 'Mobile'),
(8, 'Steam Deck');

-- Utilisateurs
INSERT IGNORE INTO `Utilisateurs` VALUES 
(1, 'admin', '$2b$12$vSTuqt.oQTDxdYV//5/Klet.s8w90XQvoxbITObLP4Gb2LUu0O0E2', 'Admin', NOW()),
(2, 'alice', '$2b$12$FuJA4bKj6XG/CpDW5Gb3fe8RNG4YlIgcmw9lZBRvWrflAcfw/b3Ya', 'Utilisateur', NOW()),
(3, 'bob', '$2b$12$3h5CK/HSd5Tc/jjEwhfC1u42MII88HdKw47USXdVhpQTHSxL6Kjlq', 'Utilisateur', NOW());

-- 2. Tables avec dépendances de premier niveau
-- Jeux (dépend de Genres, Editeurs, Plateformes, Utilisateurs)
INSERT IGNORE INTO `Jeux` VALUES 
(1, 'The Legend of Zelda: Tears of the Kingdom', 'La suite de Breath of the Wild', 50, 2, 1, 4, 1),
(2, 'God of War Ragnarök', 'La suite des aventures de Kratos et Atreus', 40, 1, 2, 2, 1),
(3, 'Cyberpunk 2077', 'RPG futuriste en monde ouvert', 60, 3, 7, 1, 1),
(4, 'FIFA 23', 'Simulation de football', 30, 5, 4, 2, 2),
(5, 'Resident Evil 4 Remake', 'Remake du classique survival horror', 20, 10, 10, 2, 1),
(6, 'Super Mario Wonder', 'Nouvelle aventure Mario en 2D', 15, 9, 1, 4, 2),
(7, 'Starfield', 'RPG spatial de Bethesda', 100, 3, 8, 3, 1),
(8, 'Final Fantasy XVI', 'Action-RPG dans un monde fantastique', 45, 3, 6, 2, 3),
(9, 'Call of Duty: Modern Warfare III', 'FPS multijoueur', 8, 4, 5, 1, 2),
(10, 'Assassin''s Creed Mirage', 'Action-aventure au Moyen-Orient', 30, 1, 3, 2, 1);

-- 3. Tables avec dépendances de deuxième niveau
-- ListePerso (dépend de Utilisateurs et Jeux)
INSERT IGNORE INTO `ListePerso` VALUES 
(1, 2, 1, NOW(), 'En cours', 'Super jeu, graphismes magnifiques !'),
(2, 2, 3, NOW(), 'Terminé', 'Histoire captivante'),
(3, 3, 2, NOW(), 'Non commencé', 'À commencer dès que possible'),
(4, 3, 5, NOW(), 'Abandonné', 'Trop effrayant pour moi'),
(5, 1, 7, NOW(), 'En cours', 'Exploration spatiale fascinante');

-- 4. Tables avec dépendances de troisième niveau
-- JeuxPersoManuels (dépend de ListePerso)
INSERT IGNORE INTO `JeuxPersoManuels` VALUES 
(1, 1, 'Jeu Indie Cool', 'Un petit jeu indépendant découvert sur itch.io', 'Plateforme', 'Studio Indépendant', 'PC'),
(2, 3, 'RPG Maker Project', 'Un RPG fait maison', 'RPG', 'Amateur', 'PC');

-- PartagesJeux (dépend de Utilisateurs et ListePerso)
INSERT IGNORE INTO `PartagesJeux` VALUES 
(1, 2, 3, 1, 'Tu devrais essayer ce jeu !', NOW()),
(2, 3, 2, 3, 'Un must-have selon moi', NOW());

-- SuggestionsJeux (dépend de Genres, Editeurs, Plateformes, Utilisateurs)
INSERT IGNORE INTO `SuggestionsJeux` VALUES 
(1, 'Spider-Man 2', 'Suite des aventures de Spider-Man sur PS5', 1, 2, 2, 2, 25, NOW()),
(2, 'Hollow Knight: Silksong', 'Suite très attendue de Hollow Knight', 9, 1, 1, 3, 30, NOW()),
(3, 'Final Fantasy VII Rebirth', 'Deuxième partie du remake', 3, 6, 2, 2, 40, NOW());

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-08 14:01:21
