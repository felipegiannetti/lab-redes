import java.net.*;

public class ServidorUDP {
    public static void main(String[] args) throws Exception {
        int porta = 5001;
        byte[] buffer = new byte[1024];

        try (DatagramSocket socket = new DatagramSocket(porta)) {
            System.out.println("[UDP] Servidor aguardando datagramas na porta " + porta + "...");
            while (true) {
                DatagramPacket pacoteRecebido = new DatagramPacket(buffer, buffer.length);
                socket.receive(pacoteRecebido);

                String mensagem = new String(pacoteRecebido.getData(), 0, pacoteRecebido.getLength());
                System.out.println("[UDP] Recebido de " + pacoteRecebido.getAddress() + ": " + mensagem);

                String resposta = "Monitor responde: recebi sua mensagem -> \"" + mensagem + "\"";
                byte[] dadosResposta = resposta.getBytes();
                DatagramPacket pacoteResposta = new DatagramPacket(
                        dadosResposta, dadosResposta.length,
                        pacoteRecebido.getAddress(), pacoteRecebido.getPort());
                socket.send(pacoteResposta);
            }
        }
    }
}
