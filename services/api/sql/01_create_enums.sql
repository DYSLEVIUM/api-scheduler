DO $$ BEGIN
    CREATE TYPE httpmethods AS ENUM (
        'GET',
        'POST',
        'PUT',
        'DELETE',
        'PATCH',
        'OPTIONS',
        'HEAD'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE jobstatus AS ENUM (
        'success',
        'timeout',
        'dns_error',
        'connection_error',
        'http_4xx',
        'http_5xx',
        'error'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
