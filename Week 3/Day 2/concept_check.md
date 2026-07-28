## Concept Check: SQL Joins & Relational Database Analysis


### 1. Why do relational databases split data into multiple tables?

Relational databases split data into multiple tables to reduce data duplication, improve consistency, and organize related information efficiently. Instead of storing the same information repeatedly, related tables are connected using Primary Keys and Foreign Keys.

---

### 2. What is the difference between INNER JOIN and LEFT JOIN?

**INNER JOIN** returns only the rows that have matching values in both tables.

**LEFT JOIN** returns all rows from the left table and the matching rows from the right table. If there is no matching row in the right table, the result contains `NULL` values.

---

### 3. When would you use a FULL OUTER JOIN?

A **FULL OUTER JOIN** is used when you want to retrieve all records from both tables, including matching and non-matching rows. If a row has no match in either table, the missing values are filled with `NULL`.

---

### 4. Why are Primary Keys and Foreign Keys important?

A **Primary Key** uniquely identifies each record in a table, ensuring that every row is unique.

A **Foreign Key** references the Primary Key of another table, creating relationships between tables and maintaining data integrity.

Together, they enable efficient data retrieval and prevent invalid or inconsistent data.

---

### 5. Explain normalization in simple words.

Normalization is the process of organizing data into multiple related tables to eliminate duplicate information and improve data consistency.

For example, customer information is stored once in the `customer` table instead of being repeated for every rental or payment.

---

### 6. What is an ER Diagram?

An **Entity Relationship (ER) Diagram** is a visual representation of a database. It shows the tables, their attributes, Primary Keys, Foreign Keys, and the relationships between them. It serves as a blueprint for understanding how the database is structured.

---

### 7. What happens if a JOIN condition is incorrect?

An incorrect JOIN condition can produce inaccurate results by matching unrelated records. It may also create duplicate rows, omit valid records, or generate a Cartesian product, where every row from one table is combined with every row from another table. Therefore, JOIN conditions should always use the correct Primary Key and Foreign Key relationships.