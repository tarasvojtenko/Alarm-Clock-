// alarm.cs - Будильник на C# Windows Forms
using System;
using System.Media;
using System.Windows.Forms;
using System.Timers;

namespace AlarmClockApp
{
    public class AlarmForm : Form
    {
        private Label timeLabel;
        private NumericUpDown hourPicker, minutePicker, secondPicker;
        private ComboBox repeatCombo;
        private Button setBtn, stopBtn, snoozeBtn;
        private Label statusLabel;
        private System.Timers.Timer clockTimer;
        private System.Timers.Timer alarmCheckTimer;
        private DateTime alarmTime;
        private string repeat;
        private bool active;
        private SoundPlayer player;

        public AlarmForm()
        {
            Text = "⏰ Будильник C#";
            Size = new System.Drawing.Size(450, 350);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = System.Drawing.Color.FromArgb(44,62,80);
            FormBorderStyle = FormBorderStyle.FixedSingle;

            // Время
            timeLabel = new Label { Font = new System.Drawing.Font("Courier New", 36, System.Drawing.FontStyle.Bold), ForeColor = System.Drawing.Color.Gold, BackColor = System.Drawing.Color.Black, TextAlign = System.Drawing.ContentAlignment.MiddleCenter, Dock = DockStyle.Top, Height = 80 };
            Controls.Add(timeLabel);

            TableLayoutPanel mainPanel = new TableLayoutPanel { RowCount = 4, ColumnCount = 2, Dock = DockStyle.Fill, Padding = new Padding(10) };
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 30));
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 70));

            mainPanel.Controls.Add(new Label { Text = "Время:", ForeColor = System.Drawing.Color.White, TextAlign = System.Drawing.ContentAlignment.MiddleRight }, 0,0);
            FlowLayoutPanel timePanel = new FlowLayoutPanel();
            hourPicker = new NumericUpDown { Minimum = 0, Maximum = 23, Width = 50, Value = 7 };
            minutePicker = new NumericUpDown { Minimum = 0, Maximum = 59, Width = 50 };
            secondPicker = new NumericUpDown { Minimum = 0, Maximum = 59, Width = 50 };
            timePanel.Controls.Add(hourPicker);
            timePanel.Controls.Add(new Label { Text = ":" });
            timePanel.Controls.Add(minutePicker);
            timePanel.Controls.Add(new Label { Text = ":" });
            timePanel.Controls.Add(secondPicker);
            mainPanel.Controls.Add(timePanel, 1,0);

            mainPanel.Controls.Add(new Label { Text = "Повтор:", ForeColor = System.Drawing.Color.White, TextAlign = System.Drawing.ContentAlignment.MiddleRight }, 0,1);
            repeatCombo = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Items = { "Один раз", "Ежедневно", "По будням" }, SelectedIndex = 0 };
            mainPanel.Controls.Add(repeatCombo, 1,1);

            FlowLayoutPanel btnPanel = new FlowLayoutPanel();
            setBtn = new Button { Text = "🔔 Установить", BackColor = System.Drawing.Color.DodgerBlue, ForeColor = System.Drawing.Color.White };
            stopBtn = new Button { Text = "🔕 Выключить", BackColor = System.Drawing.Color.Crimson, ForeColor = System.Drawing.Color.White };
            snoozeBtn = new Button { Text = "😴 Отложить (5 мин)", BackColor = System.Drawing.Color.Goldenrod, ForeColor = System.Drawing.Color.White };
            btnPanel.Controls.Add(setBtn);
            btnPanel.Controls.Add(stopBtn);
            btnPanel.Controls.Add(snoozeBtn);
            mainPanel.Controls.Add(btnPanel, 1,2);

            statusLabel = new Label { ForeColor = System.Drawing.Color.LightGray, Dock = DockStyle.Fill, TextAlign = System.Drawing.ContentAlignment.MiddleCenter };
            mainPanel.Controls.Add(statusLabel, 1,3);
            Controls.Add(mainPanel);

            setBtn.Click += SetAlarm;
            stopBtn.Click += StopAlarm;
            snoozeBtn.Click += Snooze;

            clockTimer = new System.Timers.Timer(1000);
            clockTimer.Elapsed += (s, e) => this.Invoke(new Action(() => timeLabel.Text = DateTime.Now.ToString("HH:mm:ss")));
            clockTimer.Start();

            alarmCheckTimer = new System.Timers.Timer(500);
            alarmCheckTimer.Elapsed += CheckAlarm;
            alarmCheckTimer.Start();

            active = false;
        }

        private void SetAlarm(object sender, EventArgs e)
        {
            int h = (int)hourPicker.Value;
            int m = (int)minutePicker.Value;
            int s = (int)secondPicker.Value;
            alarmTime = DateTime.Today.AddHours(h).AddMinutes(m).AddSeconds(s);
            if (alarmTime <= DateTime.Now) alarmTime = alarmTime.AddDays(1);
            repeat = repeatCombo.Text;
            active = true;
            statusLabel.Text = $"Будильник установлен на {alarmTime:HH:mm:ss} ({repeat})";
        }

        private void StopAlarm(object sender, EventArgs e)
        {
            active = false;
            if (player != null) player.Stop();
            statusLabel.Text = "Будильник выключен";
        }

        private void Snooze(object sender, EventArgs e)
        {
            if (!active) return;
            alarmTime = DateTime.Now.AddMinutes(5);
            statusLabel.Text = $"Отложено до {alarmTime:HH:mm:ss}";
            if (player != null) player.Stop();
        }

        private void CheckAlarm(object sender, ElapsedEventArgs e)
        {
            if (active)
            {
                DateTime now = DateTime.Now;
                bool ring = false;
                if (repeat == "Один раз")
                {
                    if (now >= alarmTime && (now - alarmTime).TotalSeconds < 2) ring = true;
                }
                else if (repeat == "Ежедневно")
                {
                    if (now.TimeOfDay >= alarmTime.TimeOfDay && (now - alarmTime).TotalSeconds < 2) ring = true;
                }
                else if (repeat == "По будням")
                {
                    if (now.DayOfWeek != DayOfWeek.Saturday && now.DayOfWeek != DayOfWeek.Sunday &&
                        now.TimeOfDay >= alarmTime.TimeOfDay && (now - alarmTime).TotalSeconds < 2) ring = true;
                }
                if (ring)
                {
                    this.Invoke(new Action(() => Ring()));
                }
            }
        }

        private void Ring()
        {
            player = new SoundPlayer("alarm.wav");
            try { player.PlayLooping(); } catch { System.Media.SystemSounds.Beep.Play(); }
            DialogResult res = MessageBox.Show("Время просыпаться!", "Будильник", MessageBoxButtons.OKCancel, MessageBoxIcon.Warning);
            player.Stop();
            if (repeat == "Один раз") active = false;
            else
            {
                // для повторов переустанавливаем на следующий день
                alarmTime = alarmTime.AddDays(1);
                statusLabel.Text = $"Следующий звонок: {alarmTime:HH:mm:ss}";
            }
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.Run(new AlarmForm());
        }
    }
}
