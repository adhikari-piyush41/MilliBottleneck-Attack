sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt install suricata
sudo systemctl enable suricata.service
# sudo systemctl stop suricata.service
# sudo tail -f /var/log/suricata/suricata.log