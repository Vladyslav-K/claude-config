// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
'use server';

import { db } from './db';

export async function findUser(id: string) {
  return db.query(`SELECT * FROM users WHERE id = ${id}`);
}
