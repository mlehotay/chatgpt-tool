DB_NAME = chatgpt.db
USER_FILE = user.json

.PHONY: all clean

all: $(DB_NAME)

$(DB_NAME): chatgpt_import.py
	python3 chatgpt_import.py

clean:
	rm -f $(DB_NAME)
