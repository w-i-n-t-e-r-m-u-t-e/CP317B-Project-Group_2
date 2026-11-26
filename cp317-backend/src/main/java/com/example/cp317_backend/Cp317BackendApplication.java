package com.example.cp317_backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.persistence.autoconfigure.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication(scanBasePackages = "com.devtiro.task")
@EntityScan("com.devtiro.task")
@EnableJpaRepositories("com.devtiro.task")
public class Cp317BackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(Cp317BackendApplication.class, args);
	}

}
