"""Add /edit_video command to telegram_bot.py.
Lets user iteratively refine the pending video draft via natural-language edits."""
from pathlib import Path
import sys

src = Path("telegram_bot.py")
lines = src.read_text(encoding="utf-8").splitlines(keepends=True)

# Bail if already patched
if any("edit_video_cmd" in line for line in lines):
    print("❌ Already patched (edit_video_cmd found). Aborting.")
    sys.exit(1)

# Sanity: confirm prior human-in-loop patch is present
if not any("last_video_script" in line for line in lines):
    print("❌ Prerequisite missing: /video human-in-loop patch not applied.")
    sys.exit(1)

def find_line(needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i
    return -1

# Insert new handler BEFORE cancel_video_cmd (logical grouping: confirm/reroll/edit/cancel)
cancel_def_idx = find_line("async def cancel_video_cmd")
assert cancel_def_idx >= 0, "Could not find cancel_video_cmd"

# Insert registration AFTER reroll_video registration
reroll_reg_idx = find_line("CommandHandler('reroll_video', self.reroll_video_cmd)")
assert reroll_reg_idx >= 0, "Could not find reroll_video registration"

# Update DRAFT SCRIPT / REROLLED messages to include /edit_video in the menu
draft_msg_idx = find_line("✅ /confirm_video — render + publish")
assert draft_msg_idx >= 0, "Could not find /confirm_video menu text"

rerolled_msg_idx = find_line("✅ /confirm_video  🔄 /reroll_video  🗑️ /cancel_video — 5min timeout")
assert rerolled_msg_idx >= 0, "Could not find rerolled menu text"

print(f"Found landmarks:")
print(f"  cancel def line:     {cancel_def_idx+1}")
print(f"  reroll reg line:     {reroll_reg_idx+1}")
print(f"  draft msg line:      {draft_msg_idx+1}")
print(f"  rerolled msg line:   {rerolled_msg_idx+1}")

new_lines = []
for i, line in enumerate(lines):
    # Inject edit_video_cmd handler before cancel_video_cmd
    if i == cancel_def_idx:
        edit_handler = '''    async def edit_video_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Refine the pending draft via natural-language edit instructions."""
        if not self.last_video_script or not self.last_video_topic:
            await update.message.reply_text("No active video draft. Use /video first.")
            return
        instructions = " ".join(context.args).strip()
        if not instructions:
            await update.message.reply_text(
                "Usage: /edit_video <instructions>\\n\\n"
                "Examples:\\n"
                "  /edit_video Make it 2x longer and dive deeper into mechanisms\\n"
                "  /edit_video Add a hook about REM sleep at the start\\n"
                "  /edit_video Replace galantamine with mugwort"
            )
            return
        topic = self.last_video_topic
        original = self.last_video_script
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        prompt = (
            f"You are revising a 30-second Syndicate-style biohacking video script about: {topic}.\\n\\n"
            f"ORIGINAL SCRIPT:\\n{original}\\n\\n"
            f"REVISION REQUEST:\\n{instructions}\\n\\n"
            "OUTPUT RULES (CRITICAL):\\n"
            "- Output ONLY the revised script. NO preamble.\\n"
            "- DO NOT write 'Sure', 'Here is', 'Here\\'s the revised script', or any acknowledgment.\\n"
            "- DO NOT write headings, labels, stage directions, brackets, or notes.\\n"
            "- DO NOT mention forums, posts, or that this is a script.\\n"
            "- Plain spoken prose only. Direct, technical, authoritative tone.\\n"
            "- Apply the revision request faithfully but preserve the spoken-script format.\\n"
            "- Start with a hook sentence. End with a forward-looking statement.\\n"
            "\\nBegin the revised script now:"
        )
        revised = await asyncio.to_thread(self.llm.generate_response, prompt)
        revised = self._strip_script_preamble(revised) if revised else revised
        if not revised:
            await update.message.reply_text("Could not generate revised script.")
            return
        import time as _t
        self.last_video_script = revised
        self.last_video_started_at = _t.time()
        await update.message.reply_text(
            f"✏️ EDITED (topic: {topic})\\n\\n'{revised}'\\n\\n"
            "✅ /confirm_video  🔄 /reroll_video  ✏️ /edit_video  🗑️ /cancel_video — 5min timeout"
        )

'''
        new_lines.append(edit_handler)
        new_lines.append(line)
        continue
    
    # Inject registration after reroll_video
    if i == reroll_reg_idx:
        new_lines.append(line)
        new_lines.append("        application.add_handler(CommandHandler('edit_video', self.edit_video_cmd))\n")
        continue
    
    # Update draft message menu to include /edit_video
    if i == draft_msg_idx:
        new_lines.append('            "✅ /confirm_video — render + publish\\n"\n')
        # Skip until we hit the line with /reroll_video
        continue
    
    # Update rerolled message menu to include /edit_video
    if i == rerolled_msg_idx:
        new_lines.append('            "✅ /confirm_video  🔄 /reroll_video  ✏️ /edit_video  🗑️ /cancel_video — 5min timeout"\n')
        continue
    
    new_lines.append(line)

# Insert /edit_video into the draft script menu (one extra line after /reroll_video — discard...)
# Find where /reroll_video text was in our new output, then inject /edit_video below it
final_text = "".join(new_lines)

# Add /edit_video line into the initial draft menu (after /reroll_video, before /cancel_video)
old_menu = '''            "🔄 /reroll_video — regenerate script, same topic\\n"
            "🗑️ /cancel_video — discard\\n\\n"'''
new_menu = '''            "🔄 /reroll_video — regenerate script, same topic\\n"
            "✏️ /edit_video <instructions> — refine via natural language\\n"
            "🗑️ /cancel_video — discard\\n\\n"'''

if final_text.count(old_menu) == 1:
    final_text = final_text.replace(old_menu, new_menu, 1)
else:
    print(f"⚠️ Could not find draft menu to update (count={final_text.count(old_menu)}). Skipping menu addition.")

# Backup + write
original_content = "".join(lines)
backup = Path("telegram_bot.py.bak-before-editvideo-20260516")
backup.write_text(original_content, encoding="utf-8")
src.write_text(final_text, encoding="utf-8")

print(f"\nPATCH APPLIED")
print(f"  Backup: {backup.name}")
print(f"  Old: {len(original_content)} bytes")
print(f"  New: {len(final_text)} bytes")
print(f"  Delta: +{len(final_text) - len(original_content)} bytes")
