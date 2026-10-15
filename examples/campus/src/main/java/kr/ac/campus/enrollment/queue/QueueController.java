package kr.ac.campus.enrollment.queue;

import java.security.Principal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/enrollment-queue")
class QueueController {
    private final EnrollmentQueue queue;
    QueueController(EnrollmentQueue queue) { this.queue = queue; }
    @PostMapping
    EnrollmentQueue.Ticket join(Principal user) { return queue.join(user.getName()); }
    @GetMapping("/{ticket}")
    EnrollmentQueue.Ticket poll(Principal user, @PathVariable String ticket) { return queue.poll(user.getName(), ticket); }
    @DeleteMapping("/{ticket}")
    void release(Principal user, @PathVariable String ticket) { queue.cancel(user.getName(), ticket); }
}
