#!/usr/bin/env node
// YouTube PO token (cold start) uretici.
// Kullanim: node get_pot.mjs <visitor_id>
// Cikti: "mweb+<base64_token>" (yt-dlp po_token formatinda)
import { createColdStartToken } from 'bgutils-js/webpo';

const visitorId = process.argv[2];
if (!visitorId) {
  process.stderr.write('visitor_id gerekli\n');
  process.exit(1);
}

const token = createColdStartToken(visitorId);
process.stdout.write('mweb+' + token + '\n');
