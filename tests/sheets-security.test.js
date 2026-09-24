'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const { assertDestructiveOperation } = require('../sheets');
const { main } = require('../sheets-cli');

function restoreEnvironment(name, originalValue) {
    if (originalValue === undefined) {
        delete process.env[name];
    } else {
        process.env[name] = originalValue;
    }
}

test('npm start target prints help without credentials or Google dependencies', async () => {
    const output = [];
    const originalLog = console.log;
    console.log = (message) => output.push(message);
    try {
        await main([]);
    } finally {
        console.log = originalLog;
    }
    assert.match(output.join('\n'), /기본 실행은 어떤 데이터도 변경하지 않습니다/);
});

test('destructive operations require the environment flag', () => {
    assert.throws(
        () => assertDestructiveOperation('sheet-123', 'sheet-123', {}),
        /GOOGLE_SHEETS_ALLOW_DESTRUCTIVE=true/
    );
});

test('destructive operations require an exact sheet id confirmation', () => {
    const env = { GOOGLE_SHEETS_ALLOW_DESTRUCTIVE: 'true' };
    assert.throws(
        () => assertDestructiveOperation('sheet-123', 'sheet-456', env),
        /정확히 일치/
    );
    assert.doesNotThrow(
        () => assertDestructiveOperation('sheet-123', 'sheet-123', env)
    );
});

test('clear is rejected before credentials or network access', async () => {
    const originalId = process.env.GOOGLE_SPREADSHEET_ID;
    const originalCredentials = process.env.GOOGLE_APPLICATION_CREDENTIALS;
    const originalFlag = process.env.GOOGLE_SHEETS_ALLOW_DESTRUCTIVE;
    process.env.GOOGLE_SPREADSHEET_ID = 'sheet-123';
    delete process.env.GOOGLE_APPLICATION_CREDENTIALS;
    delete process.env.GOOGLE_SHEETS_ALLOW_DESTRUCTIVE;
    try {
        await assert.rejects(
            () => main(['clear', '--confirm-sheet-id', 'sheet-123']),
            /GOOGLE_SHEETS_ALLOW_DESTRUCTIVE=true/
        );
    } finally {
        restoreEnvironment('GOOGLE_SPREADSHEET_ID', originalId);
        restoreEnvironment('GOOGLE_APPLICATION_CREDENTIALS', originalCredentials);
        restoreEnvironment('GOOGLE_SHEETS_ALLOW_DESTRUCTIVE', originalFlag);
    }
});

test('delete-row is rejected when the confirmation id differs', async () => {
    const originalId = process.env.GOOGLE_SPREADSHEET_ID;
    const originalCredentials = process.env.GOOGLE_APPLICATION_CREDENTIALS;
    const originalFlag = process.env.GOOGLE_SHEETS_ALLOW_DESTRUCTIVE;
    process.env.GOOGLE_SPREADSHEET_ID = 'sheet-123';
    process.env.GOOGLE_SHEETS_ALLOW_DESTRUCTIVE = 'true';
    delete process.env.GOOGLE_APPLICATION_CREDENTIALS;
    try {
        await assert.rejects(
            () => main(['delete-row', '0', '--confirm-sheet-id', 'wrong-sheet']),
            /정확히 일치/
        );
    } finally {
        restoreEnvironment('GOOGLE_SPREADSHEET_ID', originalId);
        restoreEnvironment('GOOGLE_APPLICATION_CREDENTIALS', originalCredentials);
        restoreEnvironment('GOOGLE_SHEETS_ALLOW_DESTRUCTIVE', originalFlag);
    }
});
