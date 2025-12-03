# Queries for custdev table
create_custdev_query = """
INSERT INTO custdev (state_id, questions_id, result)
VALUES (:state_id, :questions_id, :result)
RETURNING id;
"""

get_all_custdev_query = """
SELECT * FROM custdev
"""

# Queries for custdev_questions table
create_questions_query = """
INSERT INTO custdev_questions (questions)
VALUES (:questions)
RETURNING id;
"""

get_questions_by_id_query = """
SELECT * FROM custdev_questions
WHERE id = :questions_id;
"""

get_all_questions_query = """
SELECT * FROM custdev_questions
"""

delete_questions_query = """
DELETE FROM custdev_questions
WHERE id = :questions_id;
"""
