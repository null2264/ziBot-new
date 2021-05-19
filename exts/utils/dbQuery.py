# Just bunch of SQL query
createCommandsTable = """
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER NOT NULL PRIMARY KEY UNIQUE,
        name TEXT,
        content TEXT,
        uses INTEGER DEFAULT 0,
        ownerId INTEGER,
        createdAt REAL,
        FOREIGN KEY ("id") REFERENCES guilds ("id") ON DELETE CASCADE
    );
"""

createCommandsLookupTable = """
    CREATE TABLE IF NOT EXISTS commands_lookup (
        cmdId INTEGER NOT NULL,
        name TEXT,
        guildId INTEGER,
        FOREIGN KEY ("cmdId") REFERENCES commands ("id") ON DELETE CASCADE
    );
"""

createGuildsTable = """
    CREATE TABLE IF NOT EXISTS guilds (
        id INTEGER NOT NULL PRIMARY KEY UNIQUE
    )
"""

insertToGuilds = "INSERT OR IGNORE INTO guilds (id) VALUES (:id)"
