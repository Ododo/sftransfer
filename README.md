# ftransfer
File transfer with several transport ways and security options.



# What can i do with this program

     This program, largely inspired by magic wormhole (https://github.com/warner/magic-wormhole)
     allows you to send files from one computer to another using a password and a number.
     
     This is an exemple of a session:
        sender:   send /tmp/foo password,1337
        receiver: get /tmp/bar password,1337
         
     The goal is to provide several transport ways to achieve this.
     For the moment only TCP transfer is implemented, you can use Fernet or AES to secure
     your transaction (There still are security compromises: see security details)
     The data transfer is local by default, but you can use the UPnP IGD service of your
     router (if available), to add a port forwarding to your machine and therefore, receive or send
     files from outside your lan.
     
     
# Design

     The program uses a public RendezVous server. I will host one, but you can also
     host a rendezvous server of your own. No data transit through the rendezvous server.
     
     1. The sender register itself to the rendezvous server using a TLS session.
     2. The rendezvous server store an (ip, port) couple where the sender will serve the file
        to be sent to the receiver. The server also generates and store (temporarily) a symetric key.
     3. The receiver ask the rendezvous server for the ip, port and the generated symetric key,
        still by using a TLS session.
     4. The receiver begin to read the encrypted data from the sender'socket and decrypt it (using the shared
        symetric key)
     5. File is transferred.
     
     
# Security
     
     1. I'm not a security expert, use this program at your own risk
     2. The Fernet encryption mode provides packet authentification, which means that 
        if the receiver detect that a packet is falsified, it will stop the transaction.
        However, it cannot be used with too large files (see https://cryptography.io/en/latest/fernet/#limitations)
     3. You can use AES for transferring large files but then nothing stop an attacker from sending data to the receiver,
        (and maybe indefinitely: will be fixed soon).
     4. At the moment nothing stops an attacker (with both the encryption method) from getting encrypted data
        from the sender and fake that the transaction was completed, however, those data cannot be decrypted.
     5. The server side is still vulnerable to DOS attack such as spamming put requests, i'll add a kind of timeout/blacklist
        to prevent such thing.
     6. In the server side nothing stops the stored keys to be read in-memory (do you have a solution for that ?)
     
     
 # Motivations
 
     Even though this kind of software already existed i wanted to test different ways to do it.
