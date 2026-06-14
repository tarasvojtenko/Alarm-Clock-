// alarm.go - Будильник на Go (CLI с фоновой проверкой)
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

type Alarm struct {
	Hour   int    `json:"hour"`
	Minute int    `json:"minute"`
	Second int    `json:"second"`
	Repeat string `json:"repeat"` // once, daily, weekdays
	Active bool   `json:"active"`
}

const configFile = "alarm_config.json"

var alarm Alarm
var stopChan = make(chan bool)

func main() {
	loadConfig()
	fmt.Println("⏰ Будильник на Go")
	fmt.Println("Команды: set, stop, snooze, status, exit")
	go alarmLoop()
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		cmd := strings.TrimSpace(scanner.Text())
		switch cmd {
		case "set":
			setAlarmInteractive()
		case "stop":
			stopAlarm()
		case "snooze":
			snoozeAlarm()
		case "status":
			showStatus()
		case "exit":
			saveConfig()
			stopChan <- true
			fmt.Println("До свидания!")
			return
		default:
			fmt.Println("Неизвестная команда")
		}
	}
}

func alarmLoop() {
	for {
		select {
		case <-stopChan:
			return
		default:
			if alarm.Active {
				now := time.Now()
				shouldRing := false
				if alarm.Repeat == "once" {
					if now.Hour() == alarm.Hour && now.Minute() == alarm.Minute && now.Second() == alarm.Second {
						shouldRing = true
					}
				} else if alarm.Repeat == "daily" {
					if now.Hour() == alarm.Hour && now.Minute() == alarm.Minute && now.Second() == alarm.Second {
						shouldRing = true
					}
				} else if alarm.Repeat == "weekdays" {
					if now.Weekday() != time.Saturday && now.Weekday() != time.Sunday &&
						now.Hour() == alarm.Hour && now.Minute() == alarm.Minute && now.Second() == alarm.Second {
						shouldRing = true
					}
				}
				if shouldRing {
					ring()
					if alarm.Repeat == "once" {
						alarm.Active = false
						saveConfig()
					}
				}
			}
			time.Sleep(500 * time.Millisecond)
		}
	}
}

func ring() {
	fmt.Println("\n🔔🔔🔔 БУДИЛЬНИК! 🔔🔔🔔")
	for i := 0; i < 5; i++ {
		fmt.Print("\a")
		time.Sleep(500 * time.Millisecond)
	}
	fmt.Println("\nВведите 'stop' чтобы выключить или 'snooze' для откладывания")
}

func setAlarmInteractive() {
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Час (0-23): ")
	hStr, _ := reader.ReadString('\n')
	h, _ := strconv.Atoi(strings.TrimSpace(hStr))
	fmt.Print("Минута (0-59): ")
	mStr, _ := reader.ReadString('\n')
	m, _ := strconv.Atoi(strings.TrimSpace(mStr))
	fmt.Print("Секунда (0-59): ")
	sStr, _ := reader.ReadString('\n')
	s, _ := strconv.Atoi(strings.TrimSpace(sStr))
	fmt.Print("Повтор (once/daily/weekdays): ")
	rep, _ := reader.ReadString('\n')
	rep = strings.TrimSpace(rep)
	alarm = Alarm{Hour: h, Minute: m, Second: s, Repeat: rep, Active: true}
	saveConfig()
	fmt.Printf("Будильник установлен на %02d:%02d:%02d (%s)\n", h, m, s, rep)
}

func stopAlarm() {
	alarm.Active = false
	saveConfig()
	fmt.Println("Будильник выключен")
}

func snoozeAlarm() {
	if !alarm.Active {
		fmt.Println("Будильник не активен")
		return
	}
	now := time.Now()
	newTime := now.Add(5 * time.Minute)
	alarm.Hour = newTime.Hour()
	alarm.Minute = newTime.Minute()
	alarm.Second = newTime.Second()
	alarm.Repeat = "once" // сброс повтора после snooze? Логично один раз
	fmt.Printf("Отложено на 5 минут, новый звонок в %02d:%02d:%02d\n", alarm.Hour, alarm.Minute, alarm.Second)
	saveConfig()
}

func showStatus() {
	if alarm.Active {
		fmt.Printf("Будильник активен: %02d:%02d:%02d (%s)\n", alarm.Hour, alarm.Minute, alarm.Second, alarm.Repeat)
	} else {
		fmt.Println("Будильник не активен")
	}
}

func loadConfig() {
	file, err := os.ReadFile(configFile)
	if err != nil {
		alarm = Alarm{Active: false}
		return
	}
	json.Unmarshal(file, &alarm)
}

func saveConfig() {
	data, _ := json.MarshalIndent(alarm, "", "  ")
	os.WriteFile(configFile, data, 0644)
}
