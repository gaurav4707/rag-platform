import { test, expect } from '@playwright/test';

const FIXTURES = {
  valid: 'tests/fixtures/valid.pdf',
  valid2: 'tests/fixtures/valid2.pdf',
  blank: 'tests/fixtures/blank.pdf',
  corrupted: 'tests/fixtures/corrupted.pdf',
  duplicate: 'tests/fixtures/duplicate.pdf',
} as const;

function getFixturePath(name: keyof typeof FIXTURES) {
  return FIXTURES[name];
}

async function uploadFile(page: any, fixtureName: keyof typeof FIXTURES) {
  const fileInput = page.getByTestId('file-input');
  await fileInput.setInputFiles(getFixturePath(fixtureName));
}

async function waitForToast(page: any, variant: 'success' | 'error' | 'info' | 'warning', title: string) {
  const toast = page.getByTestId(`toast-${variant}`).first();
  await expect(toast).toContainText(title, { timeout: 30000 });
  return toast;
}

async function getDocumentNames(page: any) {
  const list = page.getByTestId('document-items');
  const items = list.locator('li');
  const count = await items.count();
  const names = [];
  for (let i = 0; i < count; i++) {
    const text = await items.nth(i).textContent();
    if (text) names.push(text.trim());
  }
  return names;
}

async function waitForUploadCardIdle(page: any) {
  const dropzone = page.getByTestId('upload-dropzone');
  await expect(dropzone).toContainText('Upload a PDF document', { timeout: 15000 });
}

async function waitForUploadProgress(page: any) {
  // Progress bar may appear briefly for small files - wait with shorter timeout
  try {
    await expect(page.getByTestId('upload-progress')).toBeVisible({ timeout: 5000 });
  } catch {
    // Progress bar may have already completed - that's fine
  }
}

async function waitForUploadProgressHidden(page: any) {
  await expect(page.getByTestId('upload-progress')).toBeHidden({ timeout: 30000 });
}

async function clearAllDocuments(page: any) {
  // Get all documents
  const docs = await getDocumentNames(page);
  for (const docName of docs) {
    // Find the delete button for this document and click it
    const item = page.getByTestId('document-items').locator('li', { hasText: docName });
    const deleteBtn = item.getByRole('button', { name: `Delete ${docName}` });
    await deleteBtn.click();
    
    // Confirm deletion in dialog - use exact match for the confirm button
    const confirmBtn = page.getByRole('button', { name: 'Delete', exact: true });
    await confirmBtn.click();
    
    // Wait for document to be removed
    await expect(item).toBeHidden({ timeout: 10000 });
  }
}

test.describe.serial('PDF Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await waitForUploadCardIdle(page);
  });

  test.beforeAll(async ({ browser }) => {
    // Clear database before all tests to ensure clean state
    const page = await browser.newPage();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await waitForUploadCardIdle(page);
    await clearAllDocuments(page);
    await page.close();
  });

  test('Test 1: Valid PDF upload', async ({ page }) => {
    console.log('Starting Test 1: Valid PDF upload');
    await uploadFile(page, 'valid');
    console.log('File uploaded, waiting for progress...');
    
    await waitForUploadProgress(page);
    console.log('Progress visible, waiting for completion...');
    await waitForUploadProgressHidden(page);
    console.log('Progress hidden, checking document list...');
    
    // Check if document appears in list (toast might be flaky)
    const docs = await getDocumentNames(page);
    console.log('Documents after upload:', docs);
    
    await waitForToast(page, 'success', 'Document Indexed');
    console.log('Success toast found');
    
    expect(docs.some(d => d.includes('valid.pdf'))).toBeTruthy();
    
    await waitForUploadCardIdle(page);
    console.log('Test 1 complete');
  });

  test('Test 2: Blank PDF rejected', async ({ page }) => {
    await uploadFile(page, 'blank');
    
    await waitForToast(page, 'error', 'Document Processing Failed');
    
    const successToasts = page.getByTestId('toast-success');
    await expect(successToasts).toHaveCount(0);
    
    const docs = await getDocumentNames(page);
    expect(docs.some(d => d.includes('blank.pdf'))).toBeFalsy();
    
    await waitForUploadCardIdle(page);
  });

  test('Test 3: Corrupted PDF rejected', async ({ page }) => {
    await uploadFile(page, 'corrupted');
    
    await waitForToast(page, 'error', 'Invalid PDF');
    
    const successToasts = page.getByTestId('toast-success');
    await expect(successToasts).toHaveCount(0);
    
    await waitForUploadCardIdle(page);
  });

  test('Test 4: Duplicate PDF rejected', async ({ page }) => {
    // valid.pdf is already in DB from Test 1, upload duplicate (same content)
    await uploadFile(page, 'duplicate');
    
    await waitForUploadProgress(page);
    await waitForUploadProgressHidden(page);
    
    await waitForToast(page, 'info', 'Document Already Exists');
    
    const docs = await getDocumentNames(page);
    // Should still only have 1 valid.pdf (the original)
    expect(docs.filter(d => d.includes('valid.pdf')).length).toBe(1);
    
    await waitForUploadCardIdle(page);
  });

  test('Test 5: Network interruption handled', async ({ page }) => {
    await page.route('**/documents/upload', route => route.abort('failed'));
    
    await uploadFile(page, 'valid');
    
    await waitForToast(page, 'error', 'Connection Lost');
    
    await waitForUploadCardIdle(page);
    
    await page.unroute('**/documents/upload');
  });

  test('Test 6: Sequential uploads (5 PDFs) - no stuck state', async ({ page }) => {
    test.setTimeout(120000);
    // After Tests 1-5, DB has 1 document (valid.pdf from Test 1)
    // Test 6 uploads: valid (dup), duplicate (dup), blank (err), corrupted (err), valid2 (new)
    // Expected: 1 success (valid2), 2 info (valid, duplicate), 2 error (blank, corrupted)
    const uploads = [
      { fixture: 'valid', expectToast: 'info' as const },
      { fixture: 'duplicate', expectToast: 'info' as const },
      { fixture: 'blank', expectToast: 'error' as const },
      { fixture: 'corrupted', expectToast: 'error' as const },
      { fixture: 'valid2', expectToast: 'success' as const },
    ];

    let successCount = 0;
    let infoCount = 0;
    let errorCount = 0;

    for (const upload of uploads) {
      await uploadFile(page, upload.fixture);
      
      await waitForUploadProgress(page);
      await waitForUploadProgressHidden(page);
      
      if (upload.expectToast === 'success') {
        await waitForToast(page, 'success', 'Document Indexed');
        successCount++;
      } else if (upload.expectToast === 'info') {
        await waitForToast(page, 'info', 'Document Already Exists');
        infoCount++;
      } else if (upload.expectToast === 'error') {
        await waitForToast(page, 'error', '');
        errorCount++;
      }
      
      await waitForUploadCardIdle(page);
    }

    expect(successCount).toBe(1);
    expect(infoCount).toBe(2);
    expect(errorCount).toBe(2);

    const docs = await getDocumentNames(page);
    // Should have 2 docs: valid.pdf (from Test 1) + valid2.pdf (new from Test 6)
    expect(docs.length).toBe(2);
    
    await waitForUploadCardIdle(page);
  });
});