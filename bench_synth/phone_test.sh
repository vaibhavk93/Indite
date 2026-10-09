#!/bin/bash
# End-to-end test on the connected phone (USB debugging). Needs the indite app installed.
# 1) live dictation: dialogue_2spk.wav played into the recorder in real time (~4 min)
# 2) imports: long_15min.wav (noise stretches) and dialogue_same_gender.wav
# 3) speaker labels (2 speakers) on both dialogues; 4) pull results and score.
set -u
cd "$(dirname "$0")"
A=~/Library/Android/sdk/platform-tools/adb
PKG=com.indite.app; ACT=$PKG/com.whispercppdemo.MainActivity
D=/sdcard/Android/data/$PKG/files
$A shell mkdir -p $D/tests $D/results
$A shell rm -f "$D/results/*"
for f in dialogue_2spk.wav dialogue_same_gender.wav long_15min.wav; do $A push "$f" $D/tests/ >/dev/null; done
wait_for() {  # result file name, timeout seconds
  for _ in $(seq 1 $(( $2 / 10 ))); do $A shell "test -f '$D/results/$1.json'" && return 0; sleep 10; done
  echo "timeout waiting for $1"; return 1
}
$A shell am start -n $ACT --es test_live dialogue_2spk.wav >/dev/null
wait_for "live dialogue_2spk" 900
$A shell am start -n $ACT --es test_import dialogue_same_gender.wav >/dev/null
wait_for "dialogue_same_gender" 900
$A shell am start -n $ACT --es test_import long_15min.wav >/dev/null
wait_for "long_15min" 3600
for n in "live dialogue_2spk" "dialogue_same_gender"; do
  $A shell rm -f "'$D/results/$n.json'"
  $A shell am start -n $ACT --es test_label "'$n'" --ei k 2 >/dev/null
  wait_for "$n" 900
done
mkdir -p out/phone; $A pull $D/results/. out/phone/ >/dev/null
echo "=== live dictation (2 voices, played in real time)"
python3 phone_result.py "out/phone/live dialogue_2spk.json" out/phone/live.jsonl
python3 score.py long dialogue_turns_as_long.tsv out/phone/live.jsonl 2>/dev/null | head -1
python3 score.py diar dialogue_turns.tsv out/phone/live.jsonl | head -2
echo "=== import: two similar voices"
python3 phone_result.py out/phone/dialogue_same_gender.json out/phone/same.jsonl
python3 score.py diar dialogue_same_gender_turns.tsv out/phone/same.jsonl | head -2
echo "=== import: 15 min with noise stretches"
python3 phone_result.py out/phone/long_15min.json out/phone/long.jsonl
python3 score.py long long_15min_ref.tsv out/phone/long.jsonl
