const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');

const SPREADSHEET_ID = '1O9A2hbD86PZIoHuAs235HHzDalz779e1dT8lzs23dCQ';

// JWT 클라이언트를 생성하는 헬퍼 함수
function getServiceAccountAuth() {
    const creds_path = process.env.GOOGLE_APPLICATION_CREDENTIALS;
    if (!creds_path) {
        throw new Error('GOOGLE_APPLICATION_CREDENTIALS 환경 변수가 설정되지 않았습니다.');
    }
    const creds = require(creds_path);
    return new JWT({
        email: creds.client_email,
        key: creds.private_key,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
}

// 특정 시트 객체를 가져오는 함수
async function getSheet(sheetIndex = 0) {
    const auth = getServiceAccountAuth();
    const doc = new GoogleSpreadsheet(SPREADSHEET_ID, auth);
    await doc.loadInfo();
    return doc.sheetsByIndex[sheetIndex];
}

/**
 * (READ) 시트의 모든 행을 가져옵니다.
 */
async function getRows() {
    const sheet = await getSheet();
    const rows = await sheet.getRows();
    // 각 행의 데이터를 보기 좋은 객체로 변환
    return rows.map(row => {
        const rowData = {};
        sheet.headerValues.forEach(header => {
            rowData[header] = row.get(header);
        });
        return rowData;
    });
}

/**
 * (CREATE) 시트에 새로운 행을 추가합니다.
 * @param {object} data - 추가할 데이터. 예: { "Header1": "Value1", "Header2": "Value2" }
 */
async function addRow(data) {
    const sheet = await getSheet();
    return await sheet.addRow(data);
}

/**
 * (UPDATE) 특정 행의 데이터를 수정합니다.
 * @param {number} rowIndex - 수정할 행의 인덱스 (0부터 시작)
 * @param {object} data - 수정할 데이터. 예: { "Header1": "New Value" }
 */
async function updateRow(rowIndex, data) {
    const sheet = await getSheet();
    const rows = await sheet.getRows();
    if (rowIndex >= rows.length) {
        throw new Error('수정할 행이 존재하지 않습니다.');
    }
    const row = rows[rowIndex];
    Object.keys(data).forEach(key => {
        row.set(key, data[key]);
    });
    await row.save();
    return row;
}

/**
 * (DELETE) 특정 행을 삭제합니다.
 * @param {number} rowIndex - 삭제할 행의 인덱스 (0부터 시작)
 */
async function deleteRow(rowIndex) {
    const sheet = await getSheet();
    const rows = await sheet.getRows();
    if (rowIndex >= rows.length) {
        throw new Error('삭제할 행이 존재하지 않습니다.');
    }
    await rows[rowIndex].delete();
}

// --- 사용 예시 ---
async function runExample() {
    try {
        console.log('--- CRUD 예시 실행 ---');

        // 0. 시트 초기화 (헤더 설정 및 모든 행 삭제)
        console.log('\n0. 시트를 초기화합니다...');
        const sheet = await getSheet();
        await sheet.clear(); // 모든 행 삭제
        await sheet.setHeaderRow(['Name', 'Age', 'City']); // 헤더 설정
        console.log('시트가 초기화되고 헤더가 설정되었습니다.');

        // 1. CREATE: 새로운 행 추가
        console.log('\n1. 새로운 행을 추가합니다...');
        await addRow({ Name: 'John Doe', Age: 30, City: 'New York' });
        await addRow({ Name: 'Jane Smith', Age: 25, City: 'London' });
        console.log('2개의 행이 추가되었습니다.');

        // 2. READ: 모든 행 조회
        console.log('\n2. 모든 행을 조회합니다...');
        const allRows = await getRows();
        console.log(allRows);

        // 3. UPDATE: 첫 번째 행(John Doe)의 도시를 수정
        console.log('\n3. 첫 번째 행의 도시를 수정합니다...');
        await updateRow(0, { City: 'Tokyo' });
        console.log('수정 완료.');
        const updatedRows = await getRows();
        console.log(updatedRows);

        // 4. DELETE: 두 번째 행(Jane Smith)을 삭제
        console.log('\n4. 두 번째 행을 삭제합니다...');
        await deleteRow(1);
        console.log('삭제 완료.');
        const finalRows = await getRows();
        console.log(finalRows);

    } catch (error) {
        console.error('\n오류가 발생했습니다:', error.message);
    }
}

// 스크립트 실행
runExample();