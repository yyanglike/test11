public class Main {
    // public static void main(String[] args) {
    //     long startTime = System.currentTimeMillis();

    //     for (int i = 0; i < 2400000; i++) {
    //         if (i % 2 == 0) {
    //             double x = i * 3.124;
    //             x /= 4.52;
    //             x *= 0.21;
    //         }
    //     }

    //     long endTime = System.currentTimeMillis();

    //     System.out.println("Total execution time: " + (endTime - startTime) / 1000.0 + " seconds");
    // }

    public static void main(String[] args) {
        long startTime = System.currentTimeMillis();
        int count = 2400000;
        for (int i = 0; i < count; i++) {
    
            if (i % 5 == 1) {
                test();
            }
            if (i % 5 == 2) {
                test();
            }
            if (i % 5 == 3) {
                test();
            }
            if (i % 5 == 4) {
                test();
            }
        }
        long endTime = System.currentTimeMillis();
        System.out.println("Total execution time: " + (endTime - startTime) / 1000.0 + " seconds");
    }
    
    public static void test() {
        double x = 2*3.12;
        x /= 3;
        double y = x + 5;
    }    
}
