# משימות — PWA ל-Notion

ממשק מובייל (iPhone) למאגר המשימות ב-Notion. Notion הוא מקור האמת היחיד.

## הקמה
1. Notion → https://www.notion.so/my-integrations → צור Internal Integration, העתק את ה-token.
2. במאגר **משימות** וגם במאגר **הקורסים**: `•••` → Connections → הוסף את ה-integration.
   (בלי חיבור למאגר הקורסים — שמות הקורסים לא יוצגו.)
3. Vercel → New Project → הריפו הזה → **Root Directory: `tasks-pwa`**.
4. Environment Variables: `NOTION_TOKEN`, `APP_PIN` (6+ ספרות), ו-`NOTION_TASKS_DB_ID` (אופציונלי).
5. Deploy → פתח ב-Safari באייפון → שיתוף → "הוסף למסך הבית".

## פיתוח מקומי
```
cp .env.example .env.local   # למלא ערכים
npm install && npm run dev
```
