"""V2: line-based replacement of generate_video body + handler injection.
Robust against blank lines and whitespace variations."""
from pathlib import Path
import sys

src = Path("telegram_bot.py")
lines = src.read_text(encoding="utf-8").splitlines(keepends=True)

# Bail if already patched
if any("last_video_script" in line for line in lines):
    print("❌ Already patched (last_video_script found). Aborting.")
    sys.exit(1)

# Locate landmarks by content (more robust than line numbers)
def find_line(needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i
    return -1

# EDIT 1: locate "self.video = VideoCreator()"
init_idx = find_line("self.video = VideoCreator()")
assert init_idx >= 0, "Could not find self.video init line"

# EDIT 2: locate the start + end of generate_video's response handling block
content_call_idx = find_line("content = await asyncio.to_thread(self.llm.generate_response, prompt)")
assert content_call_idx >= 0, "Could not find generate_video llm call"

# End of generate_video = the line with "Could not generate script."
end_idx = find_line('"Could not generate script."', start=content_call_idx)
assert end_idx >= 0, "Could not find end of generate_video"

# EDIT 3: locate _strip_script_preamble definition
strip_def_idx = find_line("def _strip_script_preamble(self, text: str) -> str:")
assert strip_def_idx >= 0, "Could not find _strip_script_preamble"

# EDIT 4: locate /video handler registration
video_reg_idx = find_line("CommandHandler('video', self.generate_video)")
assert video_reg_idx >= 0, "Could not find /video registration"

print(f"Found landmarks:")
print(f"  init line:        {init_idx+1}")
print(f"  llm call line:    {content_call_idx+1}")
print(f"  end of /video:    {end_idx+1}")
print(f"  _strip def line:  {strip_def_idx+1}")
print(f"  /video reg line:  {video_reg_idx+1}")

# --- BUILD NEW FILE ---
new_lines = []
i = 0
while i < len(lines):
    # EDIT 1: after self.video = VideoCreator(), inject state attrs
    if i == init_idx:
        new_lines.append(lines[i])
        new_lines.append("        # Video human-in-loop state\n")
        new_lines.append("        self.last_video_script = None\n")
        new_lines.append("        self.last_video_topic = None\n")
        new_lines.append("        self.last_video_started_at = None\n")
        i += 1
        continue
    
    # EDIT 2: replace generate_video body from llm call through "Could not generate script."
    if i == content_call_idx:
        # Write the new body
        new_lines.append('        content = await asyncio.to_thread(self.llm.generate_response, prompt)\n')
        new_lines.append('        content = self._strip_script_preamble(content) if content else content\n')
        new_lines.append('        if not content:\n')
        new_lines.append('            await update.message.reply_text("Could not generate script.")\n')
        new_lines.append('            return\n')
        new_lines.append('        # Stash for human-in-loop review\n')
        new_lines.append('        import time as _t\n')
        new_lines.append('        self.last_video_script = content\n')
        new_lines.append('        self.last_video_topic = topic\n')
        new_lines.append('        self.last_video_started_at = _t.time()\n')
        new_lines.append('        await update.message.reply_text(\n')
        new_lines.append('            f"📜 DRAFT SCRIPT (topic: {topic})\\n\\n\'{content}\'\\n\\n"\n')
        new_lines.append('            "Reply:\\n"\n')
        new_lines.append('            "✅ /confirm_video — render + publish\\n"\n')
        new_lines.append('            "🔄 /reroll_video — regenerate script, same topic\\n"\n')
        new_lines.append('            "🗑️ /cancel_video — discard\\n\\n"\n')
        new_lines.append('            "⏱️ Auto-expires in 5min."\n')
        new_lines.append('        )\n')
        new_lines.append('        if context.job_queue:\n')
        new_lines.append('            context.job_queue.run_once(\n')
        new_lines.append('                self._video_draft_timeout,\n')
        new_lines.append('                300,\n')
        new_lines.append('                chat_id=update.effective_chat.id,\n')
        new_lines.append('                name=f"video_draft_timeout_{update.effective_chat.id}",\n')
        new_lines.append('            )\n')
        # Skip lines from content_call_idx through end_idx inclusive
        i = end_idx + 1
        continue
    
    # EDIT 3: before _strip_script_preamble def, inject 4 new handlers
    if i == strip_def_idx:
        handlers = '''    async def confirm_video_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Render + publish the stashed video script."""
        if not self.last_video_script:
            await update.message.reply_text("No video draft. Use /video first.")
            return
        topic = self.last_video_topic
        content = self.last_video_script
        self.last_video_script = None
        self.last_video_topic = None
        self.last_video_started_at = None
        await update.message.reply_text(f"🎥 PRODUCTION STARTED — generating voiceover + video for: {topic}")
        try:
            file_path = await self.video.generate_biohacking_snippet(topic, content)
            if file_path and file_path.endswith('.mp4'):
                await update.message.reply_video(video=open(file_path, 'rb'))
            elif file_path and file_path.endswith('.mp3'):
                await update.message.reply_audio(audio=open(file_path, 'rb'))
            else:
                await update.message.reply_text("⚠️ Issue generating snippet.")
        except Exception as e:
            await update.message.reply_text(f"❌ Video generation failed: {type(e).__name__}: {str(e)[:200]}")

    async def reroll_video_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Regenerate script for the same topic."""
        if not self.last_video_topic:
            await update.message.reply_text("No active video draft. Use /video first.")
            return
        topic = self.last_video_topic
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        prompt = (
            f"Write the spoken script ONLY for a 30-second Syndicate-style biohacking video about: {topic}. "
            "OUTPUT RULES (CRITICAL):\\n"
            "- Begin with the first sentence of the actual script. NO preamble.\\n"
            "- DO NOT write 'Sure', 'Let\\'s', 'Alright', 'Okay', 'Here is', 'Here\\'s the script', or any acknowledgment.\\n"
            "- DO NOT write headings, labels, stage directions, brackets, or notes.\\n"
            "- DO NOT mention forums, posts, or that this is a script.\\n"
            "- Plain spoken prose only. Direct, technical, authoritative tone.\\n"
            "- Target ~75 words (about 30 seconds at conversational pace).\\n"
            "- Start with a hook sentence. End with a forward-looking statement.\\n"
            f"\\nBegin the script now about: {topic}"
        )
        content = await asyncio.to_thread(self.llm.generate_response, prompt)
        content = self._strip_script_preamble(content) if content else content
        if not content:
            await update.message.reply_text("Could not regenerate script.")
            return
        import time as _t
        self.last_video_script = content
        self.last_video_started_at = _t.time()
        await update.message.reply_text(
            f"🔄 REROLLED (topic: {topic})\\n\\n'{content}'\\n\\n"
            "✅ /confirm_video  🔄 /reroll_video  🗑️ /cancel_video — 5min timeout"
        )

    async def cancel_video_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Drop the pending video draft."""
        if self.last_video_script:
            self.last_video_script = None
            self.last_video_topic = None
            self.last_video_started_at = None
            await update.message.reply_text("🗑️ Video draft discarded.")
        else:
            await update.message.reply_text("No video draft to cancel.")

    async def _video_draft_timeout(self, context: ContextTypes.DEFAULT_TYPE):
        """JobQueue callback: clear draft if still pending after 5min."""
        import time as _t
        if self.last_video_started_at and (_t.time() - self.last_video_started_at) >= 300:
            if self.last_video_script:
                self.last_video_script = None
                self.last_video_topic = None
                self.last_video_started_at = None
                try:
                    await context.bot.send_message(
                        chat_id=context.job.chat_id,
                        text="⏱️ Video draft expired (5min). Send /video again to retry."
                    )
                except Exception:
                    pass

'''
        new_lines.append(handlers)
        new_lines.append(lines[i])
        i += 1
        continue
    
    # EDIT 4: after /video registration, add 3 new handler registrations
    if i == video_reg_idx:
        new_lines.append(lines[i])
        new_lines.append("        application.add_handler(CommandHandler('confirm_video', self.confirm_video_cmd))\n")
        new_lines.append("        application.add_handler(CommandHandler('reroll_video', self.reroll_video_cmd))\n")
        new_lines.append("        application.add_handler(CommandHandler('cancel_video', self.cancel_video_cmd))\n")
        i += 1
        continue
    
    # Default: keep line as-is
    new_lines.append(lines[i])
    i += 1

# Backup + write
original_content = "".join(lines)
new_content = "".join(new_lines)

backup = Path("telegram_bot.py.bak-before-videohitl-v2-20260516")
backup.write_text(original_content, encoding="utf-8")
src.write_text(new_content, encoding="utf-8")

print(f"\nPATCH APPLIED")
print(f"  Backup:  {backup.name}")
print(f"  Old: {len(original_content)} bytes ({len(lines)} lines)")
print(f"  New: {len(new_content)} bytes ({len(new_lines)} lines)")
