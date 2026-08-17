import java.io.*;
import java.net.*;

public class ClienteTCP {
    public static void main(String[] args) throws IOException {
        String host = "localhost";
        int porta = 5000;

        try (Socket socket = new Socket(host, porta);
             PrintWriter saida = new PrintWriter(socket.getOutputStream(), true);
             BufferedReader entrada = new BufferedReader(
                     new InputStreamReader(socket.getInputStream()));
             BufferedReader teclado = new BufferedReader(new InputStreamReader(System.in))) {

            System.out.println("[TCP] Conectado ao servidor. Digite 'sair' para encerrar.");
            String linha;
            while (true) {
                System.out.print("> ");
                linha = teclado.readLine();
                saida.println(linha);
                System.out.println(entrada.readLine());
                if (linha.equalsIgnoreCase("sair")) break;
            }
        }
    }
}
