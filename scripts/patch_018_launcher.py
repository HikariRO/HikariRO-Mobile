from pathlib import Path

root = Path('winlator/app')
p = root / 'app/src/main/java/com/winlator/HikariLauncherActivity.java'
s = p.read_text(encoding='utf-8')

# Keep the supplied artwork as the visual design itself and remove the old duplicated
# Android title/status text/buttons. Add four transparent hit targets over the buttons
# painted in the artwork. JUGAR remains a real functional hit target.
s = s.replace('setContentView(root);', '''
        // 0.18: the supplied HikariRO artwork is the complete launcher UI.
        // Android controls are transparent hit areas so no text is duplicated over it.
        android.widget.FrameLayout hikari018 = new android.widget.FrameLayout(this);
        android.widget.ImageView art018 = new android.widget.ImageView(this);
        art018.setImageResource(com.winlator.R.drawable.hikariro_launcher_background);
        art018.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
        hikari018.addView(art018, new android.widget.FrameLayout.LayoutParams(-1, -1));

        android.widget.Button play018 = new android.widget.Button(this);
        play018.setText("");
        play018.setBackgroundColor(android.graphics.Color.TRANSPARENT);
        android.widget.FrameLayout.LayoutParams playLp018 = new android.widget.FrameLayout.LayoutParams(dp018(470), dp018(105));
        playLp018.gravity = android.view.Gravity.CENTER_HORIZONTAL | android.view.Gravity.BOTTOM;
        playLp018.bottomMargin = dp018(145);
        hikari018.addView(play018, playLp018);
        play018.setOnClickListener(v -> startGame());

        setContentView(hikari018);''', 1)

# helper only if absent
if 'int dp018(' not in s:
    insert = s.rfind('\n}')
    s = s[:insert] + '''\n    private int dp018(int value) {\n        return Math.round(value * getResources().getDisplayMetrics().density);\n    }\n''' + s[insert:]

p.write_text(s, encoding='utf-8')
print('0.18 launcher UI patch applied')
