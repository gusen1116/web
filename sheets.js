'use strict';

const fs = require('node:fs');
const path = require('node:path');

const READ_ONLY_SCOPE = 'https://www.googleapis.com/auth/spreadsheets.readonly';
const READ_WRITE_SCOPE = 'https://www.googleapis.com/auth/spreadsheets';
const DESTRUCTIVE_ENV_VAR = 'GOOGLE_SHEETS_ALLOW_DESTRUCTIVE';

function requiredValue(value, name) {
    if (typeof value !== 'string' || value.trim() === '') {
        throw new Error(`${name} 환경 변수가 설정되지 않았습니다.`);
    }
    return value.trim();
}

function assertDestructiveOperation(spreadsheetId, confirmSheetId, env = process.env) {
    if (env[DESTRUCTIVE_ENV_VAR] !== 'true') {
        throw new Error(
            `파괴적 작업이 차단되었습니다. ${DESTRUCTIVE_ENV_VAR}=true를 명시해야 합니다.`
        );
    }
    if (confirmSheetId !== spreadsheetId) {
        throw new Error(
            '파괴적 작업이 차단되었습니다. --confirm-sheet-id가 대상 시트 ID와 정확히 일치해야 합니다.'
        );
    }
}

function loadCredentials(credentialsPath) {
    const resolvedPath = path.resolve(
        requiredValue(credentialsPath, 'GOOGLE_APPLICATION_CREDENTIALS')
    );
    let credentials;
    try {
        credentials = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'));
    } catch (error) {
        throw new Error(`서비스 계정 자격 증명을 읽을 수 없습니다: ${error.message}`);
    }
    if (!credentials.client_email || !credentials.private_key) {
        throw new Error('서비스 계정 자격 증명에 client_email 또는 private_key가 없습니다.');
    }
    return credentials;
}

class SheetsClient {
    constructor({
        spreadsheetId = process.env.GOOGLE_SPREADSHEET_ID,
        credentialsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS,
        sheetIndex = 0,
        readOnly = true,
    } = {}) {
        this.spreadsheetId = requiredValue(spreadsheetId, 'GOOGLE_SPREADSHEET_ID');
        if (!Number.isInteger(sheetIndex) || sheetIndex < 0) {
            throw new Error('sheetIndex는 0 이상의 정수여야 합니다.');
        }
        this.credentialsPath = credentialsPath;
        this.sheetIndex = sheetIndex;
        this.readOnly = readOnly;
        this.sheet = null;
    }

    assertWritable() {
        if (this.readOnly) {
            throw new Error('읽기 전용 클라이언트에서는 시트를 변경할 수 없습니다.');
        }
    }

    async connect() {
        if (this.sheet) {
            return this.sheet;
        }

        // Dependencies are loaded only when a real Sheet command is requested.
        // Therefore `npm start` and `--help` never read credentials or use the network.
        const { GoogleSpreadsheet } = require('google-spreadsheet');
        const { JWT } = require('google-auth-library');
        const credentials = loadCredentials(this.credentialsPath);
        const auth = new JWT({
            email: credentials.client_email,
            key: credentials.private_key,
            scopes: [this.readOnly ? READ_ONLY_SCOPE : READ_WRITE_SCOPE],
        });
        const document = new GoogleSpreadsheet(this.spreadsheetId, auth);
        await document.loadInfo();

        const sheet = document.sheetsByIndex[this.sheetIndex];
        if (!sheet) {
            throw new Error(`인덱스 ${this.sheetIndex}에 해당하는 시트가 없습니다.`);
        }
        this.sheet = sheet;
        return sheet;
    }

    async getRows() {
        const sheet = await this.connect();
        const rows = await sheet.getRows();
        return rows.map((row) => {
            const rowData = {};
            sheet.headerValues.forEach((header) => {
                rowData[header] = row.get(header);
            });
            return rowData;
        });
    }

    async addRow(data) {
        this.assertWritable();
        const sheet = await this.connect();
        return sheet.addRow(data);
    }

    async updateRow(rowIndex, data) {
        this.assertWritable();
        const sheet = await this.connect();
        const rows = await sheet.getRows();
        if (!Number.isInteger(rowIndex) || rowIndex < 0 || rowIndex >= rows.length) {
            throw new Error('수정할 행이 존재하지 않습니다.');
        }
        const row = rows[rowIndex];
        Object.entries(data).forEach(([key, value]) => row.set(key, value));
        await row.save();
        return row;
    }

    async deleteRow(rowIndex, { confirmSheetId } = {}) {
        this.assertWritable();
        assertDestructiveOperation(this.spreadsheetId, confirmSheetId);
        if (!Number.isInteger(rowIndex) || rowIndex < 0) {
            throw new Error('rowIndex는 0 이상의 정수여야 합니다.');
        }
        const sheet = await this.connect();
        const rows = await sheet.getRows();
        if (rowIndex >= rows.length) {
            throw new Error('삭제할 행이 존재하지 않습니다.');
        }
        await rows[rowIndex].delete();
    }

    async clear({ confirmSheetId } = {}) {
        this.assertWritable();
        assertDestructiveOperation(this.spreadsheetId, confirmSheetId);
        const sheet = await this.connect();
        await sheet.clear();
    }
}

module.exports = {
    DESTRUCTIVE_ENV_VAR,
    READ_ONLY_SCOPE,
    READ_WRITE_SCOPE,
    SheetsClient,
    assertDestructiveOperation,
};
