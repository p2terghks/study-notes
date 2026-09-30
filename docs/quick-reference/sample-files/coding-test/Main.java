import java.io.*;
import java.util.*;

public class Main {
    static class FastInput {
        final BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer tokens;
        String next() throws IOException {
            while (tokens == null || !tokens.hasMoreTokens()) {
                String line = reader.readLine();
                if (line == null) throw new EOFException();
                tokens = new StringTokenizer(line);
            }
            return tokens.nextToken();
        }
        int nextInt() throws IOException { return Integer.parseInt(next()); }
        long nextLong() throws IOException { return Long.parseLong(next()); }
    }
    public static void main(String[] args) throws Exception {
        FastInput in = new FastInput();
        int n = in.nextInt(), q = in.nextInt();
        long[] prefix = new long[n + 1];
        for (int i = 1; i <= n; i++) prefix[i] = prefix[i - 1] + in.nextLong();
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < q; i++) {
            int left = in.nextInt(), right = in.nextInt();
            out.append(prefix[right] - prefix[left - 1]).append('\n');
        }
        System.out.print(out);
    }
}
