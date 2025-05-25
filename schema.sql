-- 1. 사용자 테이블 (laundry_user)
CREATE TABLE `laundry_user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` VARCHAR(10) NOT NULL UNIQUE,    -- 학번
  `password` VARCHAR(128) NOT NULL,            -- 해시된 비밀번호
  `is_admin` TINYINT(1) NOT NULL DEFAULT 0,    -- 관리자 여부
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 기숙사 동 테이블 (laundry_building)
CREATE TABLE `laundry_building` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(1) NOT NULL,                  -- A, B, C, D, E 동
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 세탁기/건조기 테이블 (laundry_washingmachine)
CREATE TABLE `laundry_washingmachine` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `building_id` BIGINT NOT NULL,               -- ForeignKey → laundry_building(id)
  `name` VARCHAR(100) NOT NULL,                -- 기기 이름 (예: A1)
  `is_in_use` TINYINT(1) NOT NULL DEFAULT 0,    -- 사용 중 여부
  `description` TEXT NOT NULL,                 -- 기기 설명
  PRIMARY KEY (`id`),
  KEY `idx_wm_building` (`building_id`),
  CONSTRAINT `fk_wm_building`
    FOREIGN KEY (`building_id`)
    REFERENCES `laundry_building` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 예약 테이블 (laundry_reservation)
CREATE TABLE `laundry_reservation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,                   -- ForeignKey → laundry_user(id)
  `machine_id` BIGINT NOT NULL,                -- ForeignKey → laundry_washingmachine(id)
  `start_time` DATETIME NOT NULL,              -- 예약 시작 시각
  `end_time` DATETIME NOT NULL,                -- 예약 종료 시각
  PRIMARY KEY (`id`),
  KEY `idx_res_user` (`user_id`),
  KEY `idx_res_machine` (`machine_id`),
  CONSTRAINT `fk_res_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `laundry_user` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_res_machine`
    FOREIGN KEY (`machine_id`)
    REFERENCES `laundry_washingmachine` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 대기열 테이블 (laundry_waitlist)
CREATE TABLE `laundry_waitlist` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,                   -- ForeignKey → laundry_user(id)
  `machine_id` BIGINT NOT NULL,                -- ForeignKey → laundry_washingmachine(id)
  `created_at` DATETIME NOT NULL,              -- 대기 신청 시각 (auto_now_add)
  PRIMARY KEY (`id`),
  KEY `idx_wl_user` (`user_id`),
  KEY `idx_wl_machine` (`machine_id`),
  CONSTRAINT `fk_wl_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `laundry_user` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_wl_machine`
    FOREIGN KEY (`machine_id`)
    REFERENCES `laundry_washingmachine` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 웹푸시 구독 정보 테이블 (laundry_pushsubscription)
CREATE TABLE `laundry_pushsubscription` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,                   -- ForeignKey → laundry_user(id)
  `subscription_info` JSON NOT NULL,           -- 브라우저 푸시 구독 JSON
  `created_at` DATETIME NOT NULL,              -- 구독 생성 시각 (auto_now_add)
  PRIMARY KEY (`id`),
  KEY `idx_ps_user` (`user_id`),
  CONSTRAINT `fk_ps_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `laundry_user` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;