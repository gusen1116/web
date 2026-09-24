#!/usr/bin/env node
'use strict';

function printHelp() {
    console.log(`Google Sheets 관리 도구 (기본 실행은 어떤 데이터도 변경하지 않습니다.)

사용법:
  node sheets-cli.js list [--sheet-index INDEX]
  node sheets-cli.js clear --confirm-sheet-id SHEET_ID [--sheet-index INDEX]
  node sheets-cli.js delete-row ROW_INDEX --confirm-sheet-id SHEET_ID [--sheet-index INDEX]

필수 환경 변수:
  GOOGLE_SPREADSHEET_ID
  GOOGLE_APPLICATION_CREDENTIALS

clear/delete-row 추가 안전장치:
  GOOGLE_SHEETS_ALLOW_DESTRUCTIVE=true
  --confirm-sheet-id 값이 GOOGLE_SPREADSHEET_ID와 정확히 일치해야 함
`);
}

function parseArguments(argv) {
    const args = [...argv];
    const command = args.shift() || 'help';
    const options = { command, sheetIndex: 0, confirmSheetId: undefined, rowIndex: undefined };

    if (command === 'delete-row') {
        const rawRowIndex = args.shift();
        if (rawRowIndex === undefined || !/^\d+$/.test(rawRowIndex)) {
            throw new Error('delete-row에는 0 이상의 ROW_INDEX가 필요합니다.');
        }
        options.rowIndex = Number(rawRowIndex);
    }

    while (args.length > 0) {
        const flag = args.shift();
        const value = args.shift();
        if (value === undefined) {
            throw new Error(`${flag} 값이 필요합니다.`);
        }
        if (flag === '--sheet-index' && /^\d+$/.test(value)) {
            options.sheetIndex = Number(value);
        } else if (flag === '--confirm-sheet-id') {
            options.confirmSheetId = value;
        } else {
            throw new Error(`알 수 없는 옵션입니다: ${flag}`);
        }
    }
    return options;
}

async function main(argv = process.argv.slice(2)) {
    const options = parseArguments(argv);
    if (options.command === 'help' || options.command === '--help' || options.command === '-h') {
        printHelp();
        return;
    }
    if (!['list', 'clear', 'delete-row'].includes(options.command)) {
        throw new Error(`알 수 없는 명령입니다: ${options.command}`);
    }

    // Lazy import keeps the safe default command independent from credentials,
    // Google libraries, and all remote API calls.
    const { SheetsClient } = require('./sheets');
    const client = new SheetsClient({
        sheetIndex: options.sheetIndex,
        readOnly: options.command === 'list',
    });

    if (options.command === 'list') {
        console.log(JSON.stringify(await client.getRows(), null, 2));
    } else if (options.command === 'clear') {
        await client.clear({ confirmSheetId: options.confirmSheetId });
        console.log('시트 전체 삭제가 완료되었습니다.');
    } else {
        await client.deleteRow(options.rowIndex, { confirmSheetId: options.confirmSheetId });
        console.log(`행 ${options.rowIndex} 삭제가 완료되었습니다.`);
    }
}

if (require.main === module) {
    main().catch((error) => {
        console.error(`오류: ${error.message}`);
        process.exitCode = 1;
    });
}

module.exports = { main, parseArguments, printHelp };
