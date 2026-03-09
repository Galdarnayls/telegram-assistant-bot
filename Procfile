 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/Procfile b/Procfile
index 0421bc48dbf04412f2db5fe6a76c8641e9b897dd..a0f3f39fc482a90756a92284979ec763cbcfa90b 100644
--- a/Procfile
+++ b/Procfile
@@ -1 +1 @@
-worker: python my_bot.py
+web: python my_bot.py
 
EOF
)
