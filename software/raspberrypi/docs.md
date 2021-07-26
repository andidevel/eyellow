# EYEllowCAM Project

## Configuring Raspberry Pi as Access Point

Basically follow the tutorial on:

https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md

## Starting EYEllowCAM on boot

First copy the **EYEllowCAM** software (*eyellowcam* and the *lib* folder) to */home/pi/bin/eyellowcam*
folder.

Then copy the *eyellowcam.service* to */etc/systemd/system*. After that you can start the server:

```bash
sudo systemctl start eyellowcam
```

And to enable starting on boot:

```bash
sudo systemctl enable eyellowcam
```
